"""Multi-pair trading module.

Iterates over a configurable list of trading pairs, generates a signal for
each one, and submits market orders up to a maximum number of concurrent
trades (MAX_TRADES) as a basic risk-control measure.

The ``get_signal`` function is a random placeholder — replace it with an
AI/indicator-based strategy when ready.
"""

import os
import random

from binance.client import Client

PAIRS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

MAX_TRADES = 3  # risk control

# Set to False only when ready for live trading.
SAFE_MODE = True

# Signal thresholds for the random placeholder strategy.
BUY_THRESHOLD = 0.6
SELL_THRESHOLD = 0.4

# Position-sizing parameters.
RISK_PERCENT = 0.01       # fraction of balance allocated per trade
NOTIONAL_DIVISOR = 100    # divisor applied after risk percent to keep quantities small

_client = None


def _get_client() -> Client:
    global _client
    if _client is None:
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_SECRET")
        if not api_key or not api_secret:
            raise RuntimeError(
                "BINANCE_API_KEY and BINANCE_SECRET environment variables must be set"
            )
        _client = Client(api_key, api_secret)
    return _client


def get_signal(symbol: str) -> str:  # noqa: ARG001
    """Return a trading signal for *symbol*.

    This is a simple random placeholder — replace with an AI model or
    technical-indicator strategy when ready.

    Returns
    -------
    str
        ``"BUY"``, ``"SELL"``, or ``"HOLD"``
    """
    r = random.random()
    if r > BUY_THRESHOLD:
        return "BUY"
    elif r < SELL_THRESHOLD:
        return "SELL"
    return "HOLD"


def get_balance() -> float:
    """Return the free USDT balance from the Binance account."""
    client = _get_client()
    acc = client.get_account()
    for asset in acc["balances"]:
        if asset["asset"] == "USDT":
            return float(asset["free"])
    return 0.0


def position_size(balance: float) -> float:
    """Return the order quantity for a given *balance*.

    Sizes the position at 1 % of balance divided by a notional factor of 100
    to keep individual order quantities small.
    """
    return round((balance * RISK_PERCENT) / NOTIONAL_DIVISOR, 5)  # 1% risk


def execute(symbol: str, side: str, qty: float):
    """Submit a market order for *symbol*.

    When ``SAFE_MODE`` is ``True`` the order is only simulated (printed) and
    no real order is sent to the exchange.

    Returns
    -------
    dict | None
        The Binance order response, or ``None`` on error.
    """
    if SAFE_MODE:
        print(f"[SAFE] {side} {symbol} qty={qty}")
        return {"status": "SIMULATED", "symbol": symbol, "side": side, "qty": qty}

    client = _get_client()
    try:
        order = client.create_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=qty,
        )
        print(f"{side} {symbol}")
        return order
    except Exception as e:
        print(f"Error {symbol}: {e}")
        return None


def run_multi() -> int:
    """Run one cycle of the multi-pair strategy.

    Iterates over ``PAIRS``, generates a signal for each one, and executes
    up to ``MAX_TRADES`` orders per cycle.

    Returns
    -------
    int
        The number of trades executed in this cycle.
    """
    balance = get_balance()
    active_trades = 0

    for symbol in PAIRS:
        if active_trades >= MAX_TRADES:
            break

        signal = get_signal(symbol)

        if signal == "HOLD":
            continue

        qty = position_size(balance)

        result = execute(symbol, signal, qty)

        if result:
            active_trades += 1

    return active_trades
