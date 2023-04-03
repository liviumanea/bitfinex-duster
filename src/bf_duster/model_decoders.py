from bf_duster.models import TradingPair, Ticker, Wallet
from bf_duster.symbol_parsers import parse_pair, parse_ticker_symbol
from decimal import Decimal


def decode_wallet(wallet_data) -> Wallet:
    """
    Decode a wallet from the data returned by the Bitfinex API.
    """
    return Wallet(
        type=wallet_data[0],
        currency=wallet_data[1],
        balance_available=Decimal(wallet_data[4]),
    )


def decode_pair(pair_data) -> TradingPair:
    """
    Decode a trading pair from the data returned by the Bitfinex API.
    """
    symbol = pair_data[0]
    base, quote = parse_pair(symbol)
    min_order_size = pair_data[1][3]
    max_order_size = pair_data[1][4]
    return TradingPair(
        symbol=symbol,
        base=base,
        quote=quote,
        min_order_size=Decimal(str(min_order_size)),
        max_order_size=Decimal(str(max_order_size))
    )


def decode_ticker(d: list) -> Ticker:
    """
    Decode a ticker from the data returned by the Bitfinex API.
    """
    symbol = d[0]
    base, quote = parse_ticker_symbol(symbol)
    return Ticker(
        symbol=symbol,
        base=base,
        quote=quote,
        last_price=Decimal(str(d[7])),
    )
