from bf_duster.models import Wallet, Ticker, TradingPair
from bf_duster.steps import _create_sell_transaction, _create_buy_transaction, _create_order_transaction
from unittest.mock import MagicMock, patch


def test_create_sell_transaction():

    w = Wallet(
        type="exchange",
        currency="BTC",
        balance_available=1.0,
    )

    pair = TradingPair(
        symbol="tBTCUSD",
        base="BTC",
        quote="USD",
        min_order_size=0.006,
        max_order_size=100.0,
    )

    ticker = Ticker(
        symbol="tBTCUSD",
        base="BTC",
        quote="USD",
        last_price=27000.0,
    )

    t = _create_sell_transaction(w, pair, ticker)

    assert t.type == "EXCHANGE MARKET"
    assert t.trading_symbol == "tbtcusd"
    assert t.amount == -1.0
    assert t.success is False
    assert t.message is None

    w.balance_available = 0.005
    t = _create_sell_transaction(w, pair, ticker)

    assert t is None, "Should not be able to create a sell order with less than min order size"


def test_create_buy_transaction():

    pair = TradingPair(
        symbol="tBTCUSD",
        base="BTC",
        quote="USD",
        min_order_size=0.006,
        max_order_size=100.0,
    )

    ticker = Ticker(
        symbol="tBTCUSD",
        base="BTC",
        quote="USD",
        last_price=27000.0,
    )

    w = Wallet(
        type="exchange",
        currency="USD",
        balance_available=27000.0,
    )

    t = _create_buy_transaction(w, pair, ticker)

    assert t.type == "EXCHANGE MARKET"
    assert t.trading_symbol == "tbtcusd"
    assert t.success is False
    assert t.message is None

    w.balance_available = 10
    t = _create_buy_transaction(w, pair, ticker)
    assert t is None, "Should not be able to create a buy order with less than min order size"


def test_create_order_transaction():
    w = Wallet(
        type="exchange",
        currency="USD",
        balance_available=27000.0,
    )
    market_index = MagicMock()
    market_index.find_pairs.return_value = [
        TradingPair(
            symbol="tBTCUSD",
            base="BTC",
            quote="USD",
            min_order_size=0.006,
            max_order_size=100.0,
        ),
    ]
    market_index.get_ticker.return_value = Ticker(
        symbol="tBTCUSD",
        base="BTC",
        quote="USD",
        last_price=27000.0,
    )

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
