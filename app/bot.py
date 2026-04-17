import time

from agents.meta_brain import meta_brain
from app.execution import execute_trade

TRADING_SYMBOL = "BTCUSDT"
TRADING_LOOP_INTERVAL_SECONDS = 10


def run_bot():
    print("🚀 BOT RUNNING")

    while True:
        symbol = TRADING_SYMBOL

        # TODO: replace placeholder state with real market data fetched from
        # the exchange.  All keys below are required by the meta-brain.
        state = {
            "close": 0.0,
            "ema": 0.0,
            "ema_prev": 0.0,
            "adx": 0.0,
            "atr": 0.0,
            "atr_mean": 0.0,
            "rsi": 50.0,
        }
        # TODO: replace placeholder next_price with the real next-bar price
        # (e.g. from a live feed) once real market data is wired in.
        next_price = state["close"]

        # Guard: skip trading until real market data is available.
        if state["close"] == 0.0:
            time.sleep(TRADING_LOOP_INTERVAL_SECONDS)
            continue

        signal = meta_brain(state, next_price)

        if signal != "HOLD":
            execute_trade(symbol, signal)

        time.sleep(TRADING_LOOP_INTERVAL_SECONDS)
