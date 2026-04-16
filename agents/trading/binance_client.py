import os

from binance.client import Client

API_KEY = os.environ.get("BINANCE_API_KEY", "")
API_SECRET = os.environ.get("BINANCE_API_SECRET", "")

client = Client(API_KEY, API_SECRET)

def get_balance():
    return client.get_account()

def place_order(symbol="BTCUSDT", side="BUY", quantity=0.001):
    order = client.create_order(
        symbol=symbol,
        side=side,
        type="MARKET",
        quantity=quantity
    )
    return order
