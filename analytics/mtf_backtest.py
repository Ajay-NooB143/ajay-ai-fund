"""Multi-timeframe backtest engine with take-profit / stop-loss exits."""

from analytics.indicators import ema, rsi

WARMUP_PERIOD = 50
INITIAL_BALANCE = 1000
STOP_LOSS = 0.02
TAKE_PROFIT = 0.04


def check_exit(entry_price, current_price):
    """Return an exit reason or ``None`` if the position should stay open.

    Parameters
    ----------
    entry_price:
        The price at which the position was opened.
    current_price:
        The latest price.

    Returns
    -------
    str or None
        ``"TAKE_PROFIT"``, ``"STOP_LOSS"``, or ``None``.
    """
    profit = (current_price - entry_price) / entry_price

    if profit >= TAKE_PROFIT:
        return "TAKE_PROFIT"

    if profit <= -STOP_LOSS:
        return "STOP_LOSS"

    return None


def mtf_backtest(df, initial_balance=INITIAL_BALANCE, warmup=WARMUP_PERIOD,
                 stop_loss=STOP_LOSS, take_profit=TAKE_PROFIT):
    """Run a simple RSI-based backtest with TP / SL exits.

    Parameters
    ----------
    df:
        OHLCV DataFrame (must contain a ``"Close"`` column).
    initial_balance:
        Starting simulated balance.
    warmup:
        Number of bars to skip before trading (allows indicators to warm up).
    stop_loss:
        Fractional stop-loss threshold (e.g. 0.02 = 2 %).
    take_profit:
        Fractional take-profit threshold (e.g. 0.04 = 4 %).

    Returns
    -------
    float
        Final simulated balance.
    """
    df = df.copy()
    df["RSI"] = rsi(df)
    df["EMA"] = ema(df)

    balance = initial_balance
    position = None
    entry = 0.0

    for i in range(warmup, len(df)):
        row = df.iloc[i]
        price = row["Close"]

        if row["RSI"] < 30 and position is None:
            position = "BUY"
            entry = price

        elif position == "BUY":
            profit = (price - entry) / entry

            if profit > take_profit or profit < -stop_loss:
                balance += balance * profit
                position = None

    return balance
