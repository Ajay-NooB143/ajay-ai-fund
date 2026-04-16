import os

from binance.client import Client

client = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_SECRET"))

SAFE_MODE = True


def execute_trade(symbol, side):

    price = float(client.get_symbol_ticker(symbol=symbol)["price"])

    qty = 0.001

    if SAFE_MODE:
        print(f"[SAFE] {side} {symbol}")
        return

    if side == "BUY":
        client.order_market_buy(symbol=symbol, quantity=qty)
    else:
        client.order_market_sell(symbol=symbol, quantity=qty)

    print(f"EXECUTED {side}")
