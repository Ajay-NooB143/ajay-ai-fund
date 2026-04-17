import time

import yfinance as yf

from agents.meta_brain import meta_brain
from analytics.indicators import build_state
from app.execution import execute_trade

TRADING_SYMBOL = "BTCUSDT"
TRADING_LOOP_INTERVAL_SECONDS = 10

# yfinance ticker corresponding to the Binance trading symbol.
_YF_TICKER = "BTC-USD"


def _fetch_ohlc(ticker=_YF_TICKER):
    """Download recent 1-minute OHLC data via yfinance.

    Returns ``None`` when insufficient data is available.
    """
    df = yf.download(ticker, period="1d", interval="1m", progress=False)
    if df is None or df.empty:
        return None
    # Flatten MultiIndex columns produced by newer yfinance versions
    if hasattr(df.columns, "droplevel") and df.columns.nlevels > 1:
        df.columns = df.columns.droplevel(level=1)
    df.dropna(inplace=True)
    if len(df) < 2:
        return None
    return df


def run_bot():
    print("🚀 BOT RUNNING")

    while True:
        symbol = TRADING_SYMBOL

        df = _fetch_ohlc()

        if df is None:
            print("[WARN] No market data — skipping cycle")
            time.sleep(TRADING_LOOP_INTERVAL_SECONDS)
            continue

        state = build_state(df)

        # Guard: skip trading until real market data is available.
        if state["close"] == 0.0:
            time.sleep(TRADING_LOOP_INTERVAL_SECONDS)
            continue

        # TODO: replace placeholder next_price with the real next-bar price
        # (e.g. from a live feed) once real market data is wired in.
        next_price = state["close"]

        signal = meta_brain(state, next_price)

        if signal != "HOLD":
            execute_trade(symbol, signal)

        time.sleep(TRADING_LOOP_INTERVAL_SECONDS)
