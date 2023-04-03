from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from bf_duster.models import Wallet, PricedPair
from bf_duster.steps import _create_sell_transaction, _create_buy_transaction, _create_order_transaction


@pytest.fixture
def priced_pair():
    return PricedPair(
        symbol="BTCUSD",
        base="BTC",
        quote="USD",
        min_order_size=0.006,
        max_order_size=100.0,
        last_price=27000.0,
    )


def test_create_sell_transaction(priced_pair):
    t = _create_sell_transaction(wallet_currency="BTC", balance_available=Decimal(2), pair=priced_pair)

    assert t.type == "EXCHANGE MARKET"
    assert t.trading_symbol == "tbtcusd"
    assert t.amount == -2
    assert t.success is False
    assert t.message is None

    t = _create_sell_transaction(wallet_currency="BTC", balance_available=Decimal(0.001), pair=priced_pair)
    assert t is None, "Should not be able to create a sell order with less than min order size"


def test_create_buy_transaction(priced_pair):
    t = _create_buy_transaction(wallet_currency="USD", balance_available=Decimal(1000), pair=priced_pair)

    assert t.type == "EXCHANGE MARKET"
    assert t.trading_symbol == "tbtcusd"
    assert t.amount.compare(Decimal('0.037'))
    assert t.success is False
    assert t.message is None

    t = _create_buy_transaction(wallet_currency="USD", balance_available=Decimal(1), pair=priced_pair)
    assert t is None, "Should not be able to create a buy order with less than min order size"


def test_create_order_transaction(priced_pair):
    w = Wallet(
        type="exchange",
        currency="USD",
        balance_available=27000.0,
    )
    market_index = MagicMock()
    market_index.find_pairs.return_value = [
        priced_pair
    ]

    with patch("bf_duster.steps._create_buy_transaction") as mock_create_buy, \
            patch("bf_duster.steps._create_sell_transaction") as mock_create_sell:
        mock_create_buy.return_value = None
        mock_create_sell.return_value = None
        _create_order_transaction(w, "BTC", market_index)
        mock_create_buy.assert_called_once()
        mock_create_sell.assert_not_called()

    with patch("bf_duster.steps._create_buy_transaction") as mock_create_buy, \
            patch("bf_duster.steps._create_sell_transaction") as mock_create_sell:
        mock_create_buy.return_value = None
        mock_create_sell.return_value = None
        w.currency = "BTC"
        _create_order_transaction(w, "USD", market_index)
        mock_create_buy.assert_not_called()
        mock_create_sell.assert_called_once()
