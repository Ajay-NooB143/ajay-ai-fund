"""Technical indicators used by trading strategies."""

import pandas as pd


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

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


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
