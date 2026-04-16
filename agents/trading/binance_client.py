import os
import threading

from binance.client import Client

API_KEY = os.environ.get("BINANCE_API_KEY", "")
API_SECRET = os.environ.get("BINANCE_API_SECRET", "")

_client = None
_client_lock = threading.Lock()


def _get_client():
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = Client(API_KEY, API_SECRET)
    return _client


def get_balance():
    return _get_client().get_account()


def place_order(symbol="BTCUSDT", side="BUY", quantity=0.001):
    order = _get_client().create_order(
        symbol=symbol,
        side=side,
        type="MARKET",
        quantity=quantity
    )
    return order
