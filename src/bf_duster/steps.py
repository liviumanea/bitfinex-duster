import logging

from bf_duster.errors import RepoException
from bf_duster.models import TradingPair, FundsTransferTransaction, CreateOrderTransaction
from bf_duster.models import Wallet, Ticker
from bf_duster.repo import IRepo
from bf_duster.symbol_parsers import parse_ticker_symbol

_logger = logging.getLogger(__name__)


class MarketIndex:
    """
    Indexes trading pairs by base and counter currencies and provides ticker data.
    """

    def __init__(self, pairs: list[TradingPair], tickers: list[Ticker]):
        self._base = dict()
        self._quote = dict()
        self._tickers = {t.symbol: t for t in tickers}
        for p in pairs:
            self._base.setdefault(p.base, {}).setdefault(p.quote, p)
            self._quote.setdefault(p.quote, {}).setdefault(p.base, p)

    def get_pair_by_ticker_symbol(self, ticker_symbol: str) -> TradingPair | None:
        base, quote = parse_ticker_symbol(ticker_symbol.lower())
        return self._base.get(base, {}).get(quote, None)

    def find_pairs(self, from_currency: str, to_currency: str) -> list[TradingPair]:
        """
        Find trading pairs that can be used to convert from one currency to another.
        """
        from_currency = from_currency.lower()
        to_currency = to_currency.lower()
        result = []
        r = self._base.get(from_currency, {}).get(to_currency, None)
        if r:
            result.append(r)
        r = self._quote.get(from_currency, {}).get(to_currency, None)
        if r:
            result.append(r)
        return result

    def get_ticker(self, symbol: str) -> Ticker | None:
        return self._tickers.get(symbol, None)


def process_all(repo: IRepo):
    """
    Move all funds from margin wallets to exchange wallets and then try to convert dust to btc either by converting
    directly to btc or by converting to usd first and then to btc.
    """
    margin_wallet_transactions = _process_margin_wallets(repo)
    for t in margin_wallet_transactions:
        print(t)

    tickers = repo.get_tickers()
    trading_pairs = repo.get_trading_pairs()
    trading_pair_index = MarketIndex(trading_pairs, tickers)

    # attempt to convert dust to btc or if that fails, to usd
    ignored_currencies = ['btc', 'usd']
    target_currencies = ['btc', 'usd']
    dust_transactions = _process_exchange_dust(repo, trading_pair_index, ignored_currencies, target_currencies)

    usd_wallet = None
    for w in repo.get_wallets():
        if w.currency == 'usd':
            usd_wallet = w
            break

    final_transaction = _create_order_transaction(usd_wallet, 'btc', pair_index=trading_pair_index)
    final_transactions = _process_create_order_transactions(repo, [final_transaction])

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
        ignored_currencies: list[str],
        target_currencies: list[str]
) -> list[CreateOrderTransaction]:
    """
    Create dust transactions and process them. Return a list of attempted transactions.
    """
    wallets = repo.get_wallets()
    dust_transactions = _create_dust_transactions(wallets, pair_index, ignored_currencies, target_currencies)
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
    ticker = pair_index.get_ticker(f"t{pair.symbol}")
    if ticker is None:
        _logger.warning("No ticker for %s", pair.symbol)
        return

    _logger.debug("Exchanging %s -> %s using pair %s", w.currency, to_currency, pair.symbol)

    if w.currency == pair.quote:
        return _create_buy_transaction(w, pair, ticker)
    else:
        return _create_sell_transaction(w, pair, ticker)


def _create_buy_transaction(
        w: Wallet, pair: TradingPair, ticker: Ticker
) -> CreateOrderTransaction | None:
    """
    Create a buy order transaction for a wallet and a target currency using a trading pair.
    """
    order_size = w.balance_available / ticker.last_price
    if order_size < pair.min_order_size:
        _logger.info(
            "Cannot create BUY order for %s. Minimum order size is %s %s and available "
            "balance of %s %s only allows to buy %.9f %s",
            ticker.symbol, pair.min_order_size, ticker.symbol, w.balance_available,
            w.currency, order_size, ticker.symbol
        )
        return
    return CreateOrderTransaction(
        type='EXCHANGE MARKET',
        trading_symbol=ticker.symbol,
        amount=order_size,
    )


def _create_sell_transaction(
        w: Wallet, pair: TradingPair, ticker: Ticker
) -> CreateOrderTransaction | None:
    """
    Create a sell order transaction for a wallet and a target currency using a trading pair.
    """
    if w.balance_available < pair.min_order_size:
        _logger.info(
            "Cannot create SELL order for %s. Minimum order size is %s %s and available "
            "balance is %s %s",
            w.currency, pair.min_order_size, ticker.symbol, w.balance_available, w.currency
        )
        return
    return CreateOrderTransaction(
        type='EXCHANGE MARKET',
        trading_symbol=ticker.symbol,
        amount=w.balance_available * -1,
    )
