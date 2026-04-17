import os

from binance.client import Client

API_KEY = os.environ.get("BINANCE_API_KEY", "")
API_SECRET = os.environ.get("BINANCE_API_SECRET", "")

client = Client(API_KEY, API_SECRET)


def get_balance():
    return client.get_account()


def get_non_zero_balances():
    """Return a list of assets with a non-zero free balance.

    Returns
    -------
    list[dict]
        Each entry is a dict with ``'asset'`` and ``'free'`` keys,
        filtered to only include assets where ``free > 0``.
        Returns an empty list when the account data is unavailable
        or the response is missing the expected ``'balances'`` key.
    """
    try:
        account = client.get_account()
        return [asset for asset in account["balances"] if float(asset["free"]) > 0]
    except Exception:
        return []


def place_order(symbol="BTCUSDT", side="BUY", quantity=0.001):
    order = client.create_order(
        symbol=symbol,
        side=side,
        type="MARKET",
        quantity=quantity
    )
    return order
