import os

from binance.client import Client

SAFE_MODE = True

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Client(
            os.getenv("BINANCE_API_KEY"),
            os.getenv("BINANCE_SECRET"),
        )
    return _client


def execute_trade(symbol, side):

    if SAFE_MODE:
        print(f"[SAFE] {side} {symbol}")
        return

    client = _get_client()
    price = float(client.get_symbol_ticker(symbol=symbol)["price"])

    qty = 0.001

    if side == "BUY":
        client.order_market_buy(symbol=symbol, quantity=qty)
    else:
        client.order_market_sell(symbol=symbol, quantity=qty)

    print(f"EXECUTED {side}")
