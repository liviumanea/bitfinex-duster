from bf_duster.models import FundsTransferTransaction, CreateOrderTransaction


def format_funds_transfer_transaction(t: FundsTransferTransaction) -> str:
    result = 'success' if t.success else 'failed'
    return f"""Wallet transfer:
    {t.wallet_from} {t.currency_from} -> {t.wallet_to} {t.currency_to}.
    Amount:     {t.amount:.6f}.
    Result:     {t.success}.
    Message:    {t.message} """


def format_create_order_transaction(t: CreateOrderTransaction) -> str:
    side = 'buy' if t.amount > 0 else 'sell'
    result = 'success' if t.success else 'failed'
    return f""" Order transaction:
    Type:       {t.type}
    Symbol:     {t.trading_symbol}
    Amount:     {t.amount:.9f}
    Side:       {side}
    Result:     {result}
    Message:    {t.message} """
