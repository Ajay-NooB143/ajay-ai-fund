"""Tests for the multi-timeframe data retrieval, indicators, strategy, and backtest modules."""

import pandas as pd
import numpy as np

from analytics.indicators import ema, rsi
from analytics.mtf_backtest import check_exit, mtf_backtest
from strategies.mtf_strategy import generate_signal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv(prices):
    """Build a minimal OHLCV DataFrame from a list of close prices."""
    return pd.DataFrame({
        "Open": prices,
        "High": prices,
        "Low": prices,
        "Close": prices,
        "Volume": [100] * len(prices),
    })


# ---------------------------------------------------------------------------
# Indicator tests
# ---------------------------------------------------------------------------

class TestRSI:
    def test_rsi_returns_series(self):
        df = _make_ohlcv(list(range(1, 31)))
        result = rsi(df, period=14)
        assert isinstance(result, pd.Series)
        assert len(result) == len(df)

    def test_rsi_range(self):
        np.random.seed(42)
        prices = np.cumsum(np.random.randn(100)) + 100
        df = _make_ohlcv(prices.tolist())
        result = rsi(df, period=14).dropna()
        assert (result >= 0).all()
        assert (result <= 100).all()


class TestEMA:
    def test_ema_returns_series(self):
        df = _make_ohlcv(list(range(1, 31)))
        result = ema(df, span=10)
        assert isinstance(result, pd.Series)
        assert len(result) == len(df)

    def test_ema_smooths(self):
        prices = [10.0] * 20 + [20.0] * 20
        df = _make_ohlcv(prices)
        result = ema(df, span=5)
        # After the jump the EMA should be between 10 and 20
        assert 10 < result.iloc[25] < 20


# ---------------------------------------------------------------------------
# check_exit tests
# ---------------------------------------------------------------------------

class TestCheckExit:
    def test_take_profit(self):
        assert check_exit(100, 105) == "TAKE_PROFIT"

    def test_stop_loss(self):
        assert check_exit(100, 97) == "STOP_LOSS"

    def test_hold(self):
        assert check_exit(100, 101) is None


# ---------------------------------------------------------------------------
# Strategy signal tests
# ---------------------------------------------------------------------------

class TestGenerateSignal:
    def test_hold_on_neutral_data(self):
        """With a flat price series the RSI will be NaN or ~50 → HOLD."""
        prices = [100.0] * 60
        df_short = _make_ohlcv(prices)
        df_long = _make_ohlcv(prices)
        assert generate_signal(df_short, df_long) == "HOLD"


# ---------------------------------------------------------------------------
# Backtest tests
# ---------------------------------------------------------------------------

class TestMTFBacktest:
    def test_returns_float(self):
        np.random.seed(0)
        prices = (np.cumsum(np.random.randn(200)) + 100).tolist()
        df = _make_ohlcv(prices)
        result = mtf_backtest(df, initial_balance=1000, warmup=50)
        assert isinstance(result, float)

    def test_no_negative_balance(self):
        np.random.seed(0)
        prices = (np.cumsum(np.random.randn(200)) + 100).tolist()
        df = _make_ohlcv(prices)
        result = mtf_backtest(df, initial_balance=1000, warmup=50)
        assert result > 0


# ---------------------------------------------------------------------------
# data.fetcher import test
# ---------------------------------------------------------------------------

class TestFetcherImport:
    def test_import(self):
        from data.fetcher import get_mtf_data, get_backtest_data
        assert callable(get_mtf_data)
        assert callable(get_backtest_data)
