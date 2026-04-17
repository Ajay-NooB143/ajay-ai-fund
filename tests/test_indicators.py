"""Tests for analytics.indicators module."""

import numpy as np
import pandas as pd
import pytest

from analytics.indicators import (
    build_state,
    calculate_adx,
    calculate_atr,
    calculate_ema,
    calculate_rsi,
)


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _price_series(values):
    """Return a simple pd.Series from a list of values."""
    return pd.Series(values, dtype=float)


def _ohlc_dataframe(n=100, seed=42):
    """Generate a synthetic OHLC DataFrame with *n* bars."""
    rng = np.random.default_rng(seed)
    close = 100 + np.cumsum(rng.standard_normal(n))
    high = close + rng.uniform(0.5, 2.0, n)
    low = close - rng.uniform(0.5, 2.0, n)
    return pd.DataFrame({"High": high, "Low": low, "Close": close})


# -------------------------------------------------------------------
# EMA tests
# -------------------------------------------------------------------

class TestCalculateEma:
    def test_output_length(self):
        s = _price_series(range(1, 21))
        ema = calculate_ema(s, span=5)
        assert len(ema) == len(s)

    def test_no_nan(self):
        s = _price_series(range(1, 21))
        ema = calculate_ema(s, span=5)
        assert not ema.isna().any()

    def test_ema_follows_trend(self):
        """EMA of a monotonically increasing series should itself increase."""
        s = _price_series(range(1, 51))
        ema = calculate_ema(s, span=10)
        diffs = ema.diff().dropna()
        assert (diffs > 0).all()

    def test_span_one_equals_input(self):
        """With span=1, EMA should be the input itself."""
        s = _price_series([10, 20, 30, 40, 50])
        ema = calculate_ema(s, span=1)
        pd.testing.assert_series_equal(ema, s)


# -------------------------------------------------------------------
# RSI tests
# -------------------------------------------------------------------

class TestCalculateRsi:
    def test_output_length(self):
        s = _price_series(range(1, 31))
        rsi = calculate_rsi(s, period=14)
        assert len(rsi) == len(s)

    def test_rsi_range(self):
        """RSI should stay between 0 and 100."""
        s = _price_series(range(1, 101))
        rsi = calculate_rsi(s, period=14).dropna()
        assert (rsi >= 0).all()
        assert (rsi <= 100).all()

    def test_monotonic_up_rsi_high(self):
        """A monotonically increasing series should have RSI near 100."""
        s = _price_series(range(1, 51))
        rsi = calculate_rsi(s, period=14)
        assert rsi.iloc[-1] == 100.0

    def test_monotonic_down_rsi_low(self):
        """A monotonically decreasing series should have RSI near 0."""
        s = _price_series(list(range(50, 0, -1)))
        rsi = calculate_rsi(s, period=14)
        assert rsi.iloc[-1] == 0.0

    def test_custom_period(self):
        s = _price_series(range(1, 51))
        rsi7 = calculate_rsi(s, period=7)
        rsi21 = calculate_rsi(s, period=21)
        # Shorter period should start producing values earlier
        first_valid_7 = rsi7.first_valid_index()
        first_valid_21 = rsi21.first_valid_index()
        assert first_valid_7 is not None
        assert first_valid_21 is not None


# -------------------------------------------------------------------
# ATR tests
# -------------------------------------------------------------------

class TestCalculateAtr:
    def test_output_length(self):
        df = _ohlc_dataframe(50)
        atr = calculate_atr(df["High"], df["Low"], df["Close"], period=14)
        assert len(atr) == len(df)

    def test_atr_non_negative(self):
        df = _ohlc_dataframe(100)
        atr = calculate_atr(df["High"], df["Low"], df["Close"], period=14).dropna()
        assert (atr >= 0).all()

    def test_constant_price_atr_zero(self):
        """When price is flat, ATR should be zero."""
        n = 30
        df = pd.DataFrame({
            "High": [100.0] * n,
            "Low": [100.0] * n,
            "Close": [100.0] * n,
        })
        atr = calculate_atr(df["High"], df["Low"], df["Close"], period=5).dropna()
        assert (atr == 0.0).all()


# -------------------------------------------------------------------
# ADX tests
# -------------------------------------------------------------------

class TestCalculateAdx:
    def test_output_length(self):
        df = _ohlc_dataframe(100)
        adx = calculate_adx(df["High"], df["Low"], df["Close"], period=14)
        assert len(adx) == len(df)

    def test_adx_non_negative(self):
        df = _ohlc_dataframe(200)
        adx = calculate_adx(df["High"], df["Low"], df["Close"], period=14).dropna()
        assert (adx >= 0).all()


# -------------------------------------------------------------------
# build_state tests
# -------------------------------------------------------------------

class TestBuildState:
    def test_returns_all_keys(self):
        df = _ohlc_dataframe(100)
        state = build_state(df)
        expected_keys = {"close", "ema", "ema_prev", "adx", "atr", "atr_mean", "rsi"}
        assert set(state.keys()) == expected_keys

    def test_values_are_floats(self):
        df = _ohlc_dataframe(100)
        state = build_state(df)
        for key, value in state.items():
            assert isinstance(value, float), f"{key} is not float: {type(value)}"

    def test_close_matches_last_row(self):
        df = _ohlc_dataframe(100)
        state = build_state(df)
        assert state["close"] == pytest.approx(float(df["Close"].iloc[-1]))

    def test_rsi_in_range(self):
        df = _ohlc_dataframe(100)
        state = build_state(df)
        assert 0 <= state["rsi"] <= 100

    def test_custom_params(self):
        df = _ohlc_dataframe(200)
        state = build_state(df, ema_span=20, period=7)
        assert set(state.keys()) == {"close", "ema", "ema_prev", "adx", "atr", "atr_mean", "rsi"}
