from bf_duster.models import TradingPair, Ticker
from bf_duster.steps import MarketIndex
import pytest


@pytest.mark.parametrize(
    "from_currency,to_currency,pair_count", [
        ("BTC", "USD", 2),
        ("USD", "BTC", 2),
        ("ETH", "USD", 1),
        ("BTC", "ETH", 1),
        ("BTC", "AVA", 0),
        ("MATIC", "AVA", 0),
    ]
)
def test_market_index_happy_path(from_currency, to_currency, pair_count):
    pairs = [
        TradingPair(symbol="BTC:USD", base="BTC", quote="USD", min_order_size=0.006, max_order_size=100.0),
        TradingPair(symbol="USD:BTC", base="USD", quote="BTC", min_order_size=500, max_order_size=100.0),
        TradingPair(symbol="ETH:USD", base="ETH", quote="USD", min_order_size=0.1, max_order_size=1000.0),
        TradingPair(symbol="BTC:ETH", base="BTC", quote="ETH", min_order_size=0.006, max_order_size=1000.0)
    ]

    tickers = []

    m = MarketIndex(pairs, tickers)
    p = m.find_pairs(from_currency, to_currency)
    assert len(p) == pair_count
