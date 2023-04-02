from bf_duster.errors import InvalidSymbolException


def parse_pair(symbol: str) -> tuple[str, str]:
    """
    Parse a trading pair symbol into base and quote currencies.
    """
    if ":" in symbol:
        base, quote = symbol.split(":")
        if not base or not quote:
            raise InvalidSymbolException(f"Invalid symbol: {symbol}")
    elif len(symbol) == 6:
        base = symbol[0:3]
        quote = symbol[3:]
    else:
        raise InvalidSymbolException(f"Invalid symbol: {symbol}")
    return base, quote


def parse_ticker_symbol(symbol: str) -> tuple[str, str]:
    """
    Parse a ticker symbol into base and quote currencies.
    """
    if not symbol.startswith("t"):
        raise InvalidSymbolException(f"Invalid trading symbol: {symbol}")
    symbol = symbol[1:]
    if ":" in symbol:
        base, quote = symbol.split(":")
    elif len(symbol) == 6:
        base = symbol[0:3]
        quote = symbol[3:]
    else:
        raise InvalidSymbolException(f"Invalid symbol: {symbol}")
    return base, quote
