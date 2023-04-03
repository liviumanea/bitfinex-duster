import logging
from decimal import Decimal

from bf_duster.errors import RepoException
from bf_duster.market import MarketIndex, build_market_index
from bf_duster.models import FundsTransferTransaction, CreateOrderTransaction, PricedPair
from bf_duster.models import Wallet
from bf_duster.output import format_create_order_transaction, format_funds_transfer_transaction
from bf_duster.repo import IRepo

_logger = logging.getLogger(__name__)


def process_all(repo: IRepo, max_value_usd: Decimal = Decimal('10')):
    """
    Move all funds from margin wallets to exchange wallets and then try to convert dust to btc either by converting
    directly to btc or by converting to usd first and then to btc.
    """
    margin_wallet_transactions = _process_margin_wallets(repo)
    for t in margin_wallet_transactions:
        _logger.info(
            "Wallet transfer %s %s -> %s %s. Amount: %.6f. Success: %s. Message: %s",
            t.wallet_from, t.currency_from, t.wallet_to, t.currency_to, t.amount, t.success, t.message
        )
        print(format_funds_transfer_transaction(t))

    tickers = repo.get_tickers()
    trading_pairs = repo.get_trading_pairs()
    trading_pair_index = build_market_index(trading_pairs, tickers)

    # attempt to convert dust to btc or if that fails, to usd
    ignored_currencies = ['btc', 'usd']
    target_currencies = ['btc', 'usd']
    dust_transactions = _process_exchange_dust(
        repo, trading_pair_index, max_value_usd, ignored_currencies, target_currencies
    )

    usd_tables = {'usd', 'ust'}
    usd_wallets = [w for w in repo.get_wallets() if w.currency in usd_tables]

    final_transactions = [_create_order_transaction(w, 'btc', pair_index=trading_pair_index) for w in usd_wallets]
    final_transactions = _process_create_order_transactions(repo, final_transactions)

    dust_transactions.extend(final_transactions)

    for t in dust_transactions:
        side = 'buy' if t.amount > 0 else 'sell'
        result = 'success' if t.success else 'failed'
        _logger.info(
            "Transaction %s %s %s %s",
            t.trading_symbol[1:],
            side,
            result,
            t.message
        )
        print(format_create_order_transaction(t))


def _process_margin_wallets(repo: IRepo) -> list[FundsTransferTransaction]:
    """
    Move all funds from margin wallets to exchange wallets and return a list of attempted transactions.
    """
    wallets = repo.get_wallets()

    transfer_transactions = _create_margin_to_exchange_transactions(wallets)
    for t in transfer_transactions:
        try:
            repo.transfer(t.wallet_from, t.wallet_to, t.currency_from, t.currency_to, t.amount)
            t.success = True
        except RepoException as e:
            t.message = str(e)
            t.success = False

    return transfer_transactions


def _create_margin_to_exchange_transactions(wallets: list[Wallet]) -> list[FundsTransferTransaction]:
    """
    Create a list of funds transfer transactions from margin wallets to exchange wallets.
    """
    wallets = [w for w in wallets if w.type == 'margin' if w.balance_available > 0]
    return [
        FundsTransferTransaction(
            wallet_from=w.type,
            wallet_to='exchange',
            currency_from=w.currency,
            currency_to=w.currency[:3],
            amount=w.balance_available,
        )
        for w in wallets
    ]


def _process_exchange_dust(
        repo: IRepo,
        pair_index: MarketIndex,
        max_value_usd: Decimal,
        ignored_currencies: list[str],
        target_currencies: list[str]
) -> list[CreateOrderTransaction]:
    """
    Create dust transactions and process them. Return a list of attempted transactions.
    """
    wallets = repo.get_wallets()
    dust_transactions = _create_dust_transactions(
        wallets, pair_index, max_value_usd, ignored_currencies, target_currencies
    )
    return _process_create_order_transactions(repo, dust_transactions)


def _process_create_order_transactions(
        repo: IRepo,
        transactions: list[CreateOrderTransaction]
) -> list[CreateOrderTransaction]:
    """
    Process a list of create order transactions and return the list with the success flag set and
    set an error message if the transaction fails.
    """
    for t in transactions:
        try:
            repo.create_order(t.type, t.trading_symbol, t.amount)
            t.success = True
        except RepoException as e:
            t.message = str(e)
            t.success = False
    return transactions


def _create_dust_transactions(
        wallets: list[Wallet],
        trading_pair_index: MarketIndex,
        max_value_usd: Decimal,
        ignored_currencies: list[str] = None,
        target_currencies: list[str] = None,
) -> list[CreateOrderTransaction]:
    """
    Create a list of dust transactions. A dust transaction is a transaction that converts dust to the first available
    currency from the list of target_currencies.
    """
    wallets = [w for w in wallets if w.type == 'exchange']
    wallets = [w for w in wallets if w.currency not in ignored_currencies]

    transactions = []

    for w in wallets:
        if w.balance_available == 0:
            continue

        coin_in_usd = trading_pair_index.get_value_of(w.currency, 'usd', 'btc')
        if coin_in_usd is None:
            _logger.debug("Skipping %s because it can not be priced in usd", w.currency)
            continue

        wallet_value_in_usd = coin_in_usd * w.balance_available
        if wallet_value_in_usd > max_value_usd:
            _logger.info(
                "Skipping %s. Max value is $%.6f. Wallet value is $%.6f (%.6f %s)",
                w.currency, max_value_usd, wallet_value_in_usd, w.balance_available, w.currency
            )
            continue

        # attempt to convert to one of the target currencies
        for to_currency in [c for c in target_currencies if c != w.currency]:
            transaction = _create_order_transaction(w, to_currency, trading_pair_index)
            if transaction:
                transactions.append(transaction)
                break

        _logger.debug("Could not exchange %s", w.currency)

    return transactions


def _create_order_transaction(
        w: Wallet, to_currency: str, pair_index: MarketIndex
) -> CreateOrderTransaction | None:
    """
    Create a buy or sell order transaction for a wallet and a target currency using the first available trading pair.
    """
    usable_pairs = pair_index.find_pairs(w.currency, to_currency)
    if not usable_pairs:
        return

    pair = usable_pairs[0]

    _logger.debug("Exchanging %s -> %s using pair %s", w.currency, to_currency, pair.symbol)

    if w.currency == pair.quote:
        return _create_buy_transaction(w.currency, w.balance_available, pair)
    else:
        return _create_sell_transaction(w.currency, w.balance_available, pair)


def _create_buy_transaction(
        wallet_currency: str,
        balance_available: Decimal,
        pair: PricedPair
) -> CreateOrderTransaction | None:
    """
    Create a buy order transaction for a wallet and a target currency using a trading pair.
    """
    order_size = balance_available / pair.last_price
    if order_size < pair.min_order_size:
        _logger.debug(
            "Cannot create BUY order for %s. Minimum order size is %s %s and available "
            "balance of %s %s only allows to buy %.9f %s",
            pair.symbol, pair.min_order_size, pair.symbol, balance_available,
            wallet_currency, order_size, pair.symbol
        )
        return
    return CreateOrderTransaction(
        type='EXCHANGE MARKET',
        trading_symbol=f"t{pair.symbol}",
        amount=order_size,
    )


def _create_sell_transaction(
        wallet_currency: str,
        balance_available: Decimal,
        pair: PricedPair
) -> CreateOrderTransaction | None:
    """
    Create a sell order transaction for a wallet and a target currency using a trading pair.
    """
    if balance_available < pair.min_order_size:
        _logger.debug(
            "Cannot create SELL order for %s. Minimum order size is %s %s and available "
            "balance is %s %s",
            wallet_currency, pair.min_order_size, pair.symbol, balance_available, wallet_currency
        )
        return
    return CreateOrderTransaction(
        type='EXCHANGE MARKET',
        trading_symbol=f"t{pair.symbol}",
        amount=balance_available * -1,
    )
