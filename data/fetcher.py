"""Multi-timeframe data retrieval using yfinance."""

import yfinance as yf


DEFAULT_SYMBOL = "BTC-USD"


def get_mtf_data(symbol=DEFAULT_SYMBOL, short_period="1d", short_interval="1m",
                 long_period="5d", long_interval="5m"):
    """Download multi-timeframe OHLCV data.

    Parameters
    ----------
    symbol:
        Yahoo Finance ticker symbol (default ``"BTC-USD"``).
    short_period / short_interval:
        Period and bar size for the short-timeframe DataFrame.
    long_period / long_interval:
        Period and bar size for the long-timeframe DataFrame.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        ``(df_short, df_long)`` with NaN rows removed.
    """
    df_short = yf.download(symbol, period=short_period, interval=short_interval)
    df_long = yf.download(symbol, period=long_period, interval=long_interval)

    df_short.dropna(inplace=True)
    df_long.dropna(inplace=True)

    return df_short, df_long


def get_backtest_data(symbol=DEFAULT_SYMBOL, period="7d", interval="5m"):
    """Download a single-timeframe DataFrame for backtesting.

    Parameters
    ----------
    symbol:
        Yahoo Finance ticker symbol.
    period:
        Look-back period (e.g. ``"7d"``).
    interval:
        Bar size (e.g. ``"5m"``).

    Returns
    -------
    pd.DataFrame
        OHLCV DataFrame with NaN rows removed.
    """
    df = yf.download(symbol, period=period, interval=interval)
    df.dropna(inplace=True)
    return df
