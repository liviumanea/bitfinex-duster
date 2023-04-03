from decimal import Decimal

from pydantic import BaseModel, constr


class TradingPair(BaseModel):
    symbol: constr(to_lower=True)  # Ex: BTCUSD, MATIC:USD
    base: constr(to_lower=True)
    quote: constr(to_lower=True)
    min_order_size: Decimal
    max_order_size: Decimal


class Ticker(BaseModel):
    symbol: constr(to_lower=True)  # Ex: tBTCUSD, tMATIC:USD
    base: constr(to_lower=True)
    quote: constr(to_lower=True)
    last_price: Decimal


class PricedPair(BaseModel):
    symbol: constr(to_lower=True)  # Ex: BTCUSD, MATIC:USD
    base: constr(to_lower=True)
    quote: constr(to_lower=True)
    min_order_size: Decimal
    max_order_size: Decimal
    last_price: Decimal


class Wallet(BaseModel):
    type: constr(to_lower=True)
    currency: constr(to_lower=True)
    balance_available: Decimal


class FundsTransferTransaction(BaseModel):
    wallet_from: str
    wallet_to: str
    currency_from: str
    currency_to: str
    amount: Decimal
    success: bool = False
    message: str = None


class CreateOrderTransaction(BaseModel):
    type: str
    trading_symbol: str
    amount: Decimal
    success: bool = False
    message: str = None
