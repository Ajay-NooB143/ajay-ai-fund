import os

from binance.client import Client

portfolio = {
    "balance": 1000,
    "positions": []
}


def update_balance(amount):
    portfolio["balance"] += amount


def get_balance():
    return portfolio["balance"]


def get_live_balance() -> float:
    """Fetch the free USDT balance from Binance.

    Falls back to the local in-memory balance when the Binance credentials
    are absent or the API call fails, so the bot can still run in simulation
    mode without real keys.

    Returns
    -------
    float
        Available USDT balance.
    """
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_SECRET") or os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        return get_balance()

    try:
        client = Client(api_key, api_secret)
        account = client.get_account()
        for asset in account.get("balances", []):
            if asset.get("asset") == "USDT":
                return float(asset["free"])
    except Exception as exc:
        print(f"[WARN] Could not fetch live balance from Binance: {exc}")

    return get_balance()
