import pytest

from bf_duster.errors import InvalidSymbolException
from bf_duster.symbol_parsers import parse_pair, parse_ticker_symbol


@pytest.mark.parametrize(
    "symbol,expected_base,expected_quote",
    [
        ("BTC:USD", "BTC", "USD"),
        ("AAAA:BBBB", "AAAA", "BBBB"),
        ("BTCUSD", "BTC", "USD"),
    ])
def test_parse_pair_happy_path(symbol, expected_base, expected_quote):
    base, quote = parse_pair(symbol)
    assert base == expected_base
    assert quote == expected_quote


@pytest.mark.parametrize("symbol", ["SHORT", "BTCCUSD:", ":BTCUSD", "TOOLONG"])
def test_parse_pair_fails_when_invalid(symbol):
    with pytest.raises(InvalidSymbolException):
        parse_pair(symbol)


@pytest.mark.parametrize(
    "symbol,expected_base,expected_quote",
    [
        ("tBTC:USD", "BTC", "USD"),
        ("tAAAA:BBBB", "AAAA", "BBBB"),
        ("tBTCUSD", "BTC", "USD"),
    ]
)
def test_parse_tick_symbol_happy_path(symbol, expected_base, expected_quote):
    base, quote = parse_ticker_symbol(symbol)
    assert base == expected_base
    assert quote == expected_quote


@pytest.mark.parametrize("symbol", ["BTC:USD"])
def test_parse_tick_symbol_fails_when_invalid(symbol):
    with pytest.raises(InvalidSymbolException):
        parse_ticker_symbol(symbol)
