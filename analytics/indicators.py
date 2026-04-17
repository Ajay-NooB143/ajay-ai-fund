"""Technical indicator calculations for trading strategies.

Provides RSI, EMA, ADX, and ATR computation on pandas DataFrames or
Series.  All functions accept a ``period`` (or ``span``) parameter and
return a pandas Series of the same length as the input.
"""

import pandas as pd


# -------------------------------------------------------------------
# EMA — Exponential Moving Average
# -------------------------------------------------------------------

def calculate_ema(series: pd.Series, span: int = 50) -> pd.Series:
    """Return the exponential moving average of *series*.

    Parameters
    ----------
    series : pd.Series
        Price series (typically the close price).
    span : int
        Look-back window for the EMA (default 50).
    """
    return series.ewm(span=span, adjust=False).mean()


# -------------------------------------------------------------------
# RSI — Relative Strength Index
# -------------------------------------------------------------------

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Return the Relative Strength Index of *series*.

    Parameters
    ----------
    series : pd.Series
        Price series (typically the close price).
    period : int
        Look-back window for the RSI (default 14).
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # When avg_loss is zero RS is inf → RSI correctly becomes 100.
    # When both avg_gain and avg_loss are zero RS is NaN → default to 50.
    rsi = rsi.fillna(50.0)
    return rsi


# -------------------------------------------------------------------
# ATR — Average True Range
# -------------------------------------------------------------------

def calculate_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Return the Average True Range.

    Parameters
    ----------
    high, low, close : pd.Series
        OHLC price columns.
    period : int
        Look-back window (default 14).
    """
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.rolling(window=period).mean()


# -------------------------------------------------------------------
# ADX — Average Directional Index
# -------------------------------------------------------------------

def calculate_adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Return the Average Directional Index.

    Parameters
    ----------
    high, low, close : pd.Series
        OHLC price columns.
    period : int
        Look-back window (default 14).
    """
    plus_dm = high.diff().clip(lower=0)
    minus_dm = (-low.diff()).clip(lower=0)

    # Zero out weaker DM when both are positive
    plus_dm[plus_dm < minus_dm] = 0
    minus_dm[minus_dm < plus_dm] = 0

    atr = calculate_atr(high, low, close, period)

    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

    dx = (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, float("nan")) * 100
    adx = dx.rolling(window=period).mean()
    return adx


# -------------------------------------------------------------------
# Helper — build state dict from a DataFrame
# -------------------------------------------------------------------

def build_state(df: pd.DataFrame, ema_span: int = 50, period: int = 14) -> dict:
    """Compute all indicators and return a state dict for the latest bar.

    The returned dictionary contains keys expected by the meta-brain and
    its agents: ``close``, ``ema``, ``ema_prev``, ``adx``, ``atr``,
    ``atr_mean``, and ``rsi``.

    Parameters
    ----------
    df : pd.DataFrame
        OHLC DataFrame with columns ``High``, ``Low``, ``Close``.
    ema_span : int
        EMA window (default 50).
    period : int
        Period for RSI, ATR, and ADX (default 14).
    """
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    ema_series = calculate_ema(close, span=ema_span)
    rsi_series = calculate_rsi(close, period=period)
    atr = calculate_atr(high, low, close, period=period)
    adx = calculate_adx(high, low, close, period=period)

    latest = len(df) - 1
    return {
        "close": float(close.iloc[latest]),
        "ema": float(ema_series.iloc[latest]),
        "ema_prev": float(ema_series.iloc[latest - 1]) if latest > 0 else float(ema_series.iloc[latest]),
        "adx": float(adx.iloc[latest]) if pd.notna(adx.iloc[latest]) else 0.0,
        "atr": float(atr.iloc[latest]) if pd.notna(atr.iloc[latest]) else 0.0,
        "atr_mean": float(atr.mean()) if pd.notna(atr.mean()) else 0.0,
        "rsi": float(rsi_series.iloc[latest]) if pd.notna(rsi_series.iloc[latest]) else 50.0,
    }


# -------------------------------------------------------------------
# DataFrame-based convenience functions (used by MTF modules)
# -------------------------------------------------------------------

def rsi(df: pd.DataFrame, period: int = 14, column: str = "Close") -> pd.Series:
    """Compute the Relative Strength Index (RSI).

    Parameters
    ----------
    df:
        DataFrame containing OHLCV data.
    period:
        Look-back window for the RSI calculation.
    column:
        Name of the column to compute RSI on.

    Returns
    -------
    pd.Series
        RSI values (0–100).
    """
    delta = df[column].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, float("nan"))
    result = 100 - (100 / (1 + rs))
    # When avg_loss is zero (all gains), RSI should be 100.
    result = result.fillna(100.0)
    return result


def ema(df: pd.DataFrame, span: int = 50, column: str = "Close") -> pd.Series:
    """Compute the Exponential Moving Average (EMA).

    Parameters
    ----------
    df:
        DataFrame containing OHLCV data.
    span:
        EMA span (number of periods).
    column:
        Name of the column to compute EMA on.

    Returns
    -------
    pd.Series
        EMA values.
    """
    return df[column].ewm(span=span).mean()
