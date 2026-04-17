"""Multi-timeframe (MTF) trading strategy with RSI + EMA confirmation."""

from analytics.indicators import ema, rsi

# Default thresholds
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70


def generate_signal(df_short, df_long):
    """Generate a BUY / SELL / HOLD signal using multi-timeframe confirmation.

    The strategy requires **both** timeframes to agree on trend direction
    before acting on RSI extremes:

    * **BUY** — RSI oversold on the short timeframe *and* price is above
      the EMA on both timeframes (uptrend confirmation).
    * **SELL** — RSI overbought on the short timeframe *and* price is below
      the EMA on both timeframes (downtrend confirmation).

    Parameters
    ----------
    df_short:
        Short-timeframe OHLCV DataFrame (e.g. 1-minute bars).
    df_long:
        Long-timeframe OHLCV DataFrame (e.g. 5-minute bars).

    Returns
    -------
    str
        ``"BUY"``, ``"SELL"``, or ``"HOLD"``.
    """
    df_short = df_short.copy()
    df_long = df_long.copy()

    df_short["RSI"] = rsi(df_short)
    df_short["EMA"] = ema(df_short)
    df_long["EMA"] = ema(df_long)

    last_short = df_short.iloc[-1]
    last_long = df_long.iloc[-1]

    price = last_short["Close"]
    rsi_val = last_short["RSI"]
    ema_short = last_short["EMA"]
    ema_long = last_long["EMA"]

    trend_up = price > ema_short and price > ema_long
    trend_down = price < ema_short and price < ema_long

    if rsi_val < RSI_OVERSOLD and trend_up:
        return "BUY"

    if rsi_val > RSI_OVERBOUGHT and trend_down:
        return "SELL"

    return "HOLD"
