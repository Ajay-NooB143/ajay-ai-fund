import os

from binance.client import Client

_client = None

SAFE_MODE = True


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_SECRET")
        if not api_key or not api_secret:
            raise RuntimeError(
                "BINANCE_API_KEY and BINANCE_SECRET "
                "environment variables must be set"
            )
        _client = Client(api_key, api_secret)
    return _client


def execute_trade(symbol, side):
    client = _get_client()

    price = float(client.get_symbol_ticker(symbol=symbol)["price"])

    qty = 0.001

    if SAFE_MODE:
        print(f"[SAFE] {side} {symbol} @ {price}")
        return

    if side == "BUY":
        client.order_market_buy(symbol=symbol, quantity=qty)
    else:
        client.order_market_sell(symbol=symbol, quantity=qty)

    print(f"EXECUTED {side} {symbol} @ {price}")
