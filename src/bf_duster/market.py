from decimal import Decimal

from bf_duster.models import PricedPair, TradingPair, Ticker


class MarketIndex:
    """
    Indexes trading pairs by base and counter currencies and provides ticker data.
    """

    def __init__(self, priced_pairs: list[PricedPair]):
        self._priced_pairs = {p.symbol: p for p in priced_pairs}
        self._base = dict()
        self._quote = dict()

        for p in priced_pairs:
            self._base.setdefault(p.base, {}).setdefault(p.quote, p)
            self._quote.setdefault(p.quote, {}).setdefault(p.base, p)

    def get_quotes(self, currency: str) -> dict[str, PricedPair]:
        return self._quote.get(currency.lower(), {})

    def get_bases(self, currency: str) -> dict[str, PricedPair]:
        return self._base.get(currency.lower(), {})

    def get_pair_by_symbol(self, ticker_symbol: str) -> PricedPair | None:
        return self._priced_pairs.get(ticker_symbol)

    def find_pairs(self, from_currency: str, to_currency: str) -> list[PricedPair]:
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

    def get_value_of(self, base_currency: str, quote_currency: str, try_through_currency: str = None) -> Decimal | None:
        """
        Get the value of the amount of base currency in the quote currency.
        """
        base_currency = base_currency.lower()
        quote_currency = quote_currency.lower()

        pair = self._base.get(base_currency, {}).get(quote_currency, None)
        if pair:
            return pair.last_price
        pair = self._quote.get(base_currency, {}).get(quote_currency, None)
        if pair:
            return 1 / pair.last_price

        if try_through_currency:
            try_through_currency = try_through_currency.lower()
            value_in_through = self.get_value_of(base_currency, try_through_currency)
            if value_in_through:
                value_in_quote = self.get_value_of(try_through_currency, quote_currency)
                if value_in_quote:
                    return value_in_through * value_in_quote


def build_market_index(trading_pairs: list[TradingPair], tickers: list[Ticker]) -> MarketIndex:
    """
    Build a market index from the repository.
    """
    ticker_symbols = {t.symbol: t for t in tickers}
    trading_pair_symbols = {p.symbol: p for p in trading_pairs}

    priced_pairs = []
    for t in ticker_symbols:
        ticker = ticker_symbols[t]
        s = t[1:]
        if s in trading_pair_symbols:
            trading_pair = trading_pair_symbols[s]
            priced_pairs.append(
                PricedPair(
                    symbol=s,
                    last_price=ticker.last_price,
                    base=trading_pair.base,
                    quote=trading_pair.quote,
                    min_order_size=trading_pair.min_order_size,
                    max_order_size=trading_pair.max_order_size,
                )
            )

    return MarketIndex(priced_pairs)
