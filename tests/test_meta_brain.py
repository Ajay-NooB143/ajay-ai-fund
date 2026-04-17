"""Tests for the multi-agent meta-brain system."""

import pytest

from agents.regime import (
    REGIME_DOWNTREND,
    REGIME_HIGH_VOL,
    REGIME_RANGE,
    REGIME_UPTREND,
    detect_regime,
)
from agents.trend_agent import TrendAgent
from agents.mean_agent import MeanAgent
from agents.scalper_agent import ScalperAgent
from agents.risk_agent import RiskAgent
from agents.meta_brain import compete, meta_brain
from portfolio.allocator import Allocator


# ---------------------------------------------------------------------------
# Regime detection
# ---------------------------------------------------------------------------

_BASE_STATE = {
    "close": 150.0,
    "ema": 145.0,
    "ema_prev": 140.0,
    "adx": 30.0,
    "atr": 2.0,
    "atr_mean": 2.5,
    "rsi": 50.0,
}


def _state(**overrides):
    s = dict(_BASE_STATE)
    s.update(overrides)
    return s


def test_detect_regime_uptrend():
    s = _state(ema=145.0, ema_prev=140.0, adx=30.0, atr=2.0, atr_mean=2.5)
    assert detect_regime(s) == REGIME_UPTREND


def test_detect_regime_downtrend():
    s = _state(ema=140.0, ema_prev=145.0, adx=30.0, atr=2.0, atr_mean=2.5)
    assert detect_regime(s) == REGIME_DOWNTREND


def test_detect_regime_high_vol():
    s = _state(ema=145.0, ema_prev=145.0, adx=10.0, atr=5.0, atr_mean=2.5)
    assert detect_regime(s) == REGIME_HIGH_VOL


def test_detect_regime_range():
    s = _state(ema=145.0, ema_prev=145.0, adx=10.0, atr=2.0, atr_mean=2.5)
    assert detect_regime(s) == REGIME_RANGE


# ---------------------------------------------------------------------------
# Individual agents
# ---------------------------------------------------------------------------

def test_trend_agent_buy():
    assert TrendAgent().act(_state(close=160.0, ema=150.0)) == "BUY"


def test_trend_agent_sell():
    assert TrendAgent().act(_state(close=140.0, ema=150.0)) == "SELL"


def test_mean_agent_buy():
    assert MeanAgent().act(_state(rsi=25.0)) == "BUY"


def test_mean_agent_sell():
    assert MeanAgent().act(_state(rsi=75.0)) == "SELL"


def test_mean_agent_hold():
    assert MeanAgent().act(_state(rsi=50.0)) == "HOLD"


def test_scalper_agent_valid():
    result = ScalperAgent().act(_BASE_STATE)
    assert result in ("BUY", "SELL")


def test_risk_agent_always_hold():
    assert RiskAgent().act(_BASE_STATE) == "HOLD"


# ---------------------------------------------------------------------------
# Agent competition
# ---------------------------------------------------------------------------

def test_compete_returns_best():
    state = _state(close=100.0)
    agents = {"trend": TrendAgent(), "risk": RiskAgent()}
    best, scores = compete(agents, state, next_price=110.0)
    assert best in agents
    assert set(scores.keys()) == set(agents.keys())


def test_compete_hold_scores_zero():
    state = _state(close=100.0, ema=90.0)
    agents = {"risk": RiskAgent()}
    best, scores = compete(agents, state, next_price=110.0)
    assert best == "risk"
    assert scores["risk"] == 0.0


# ---------------------------------------------------------------------------
# Meta-brain ensemble
# ---------------------------------------------------------------------------

def test_meta_brain_returns_valid_signal():
    result = meta_brain(_BASE_STATE, next_price=155.0)
    assert result in ("BUY", "SELL", "HOLD")


# ---------------------------------------------------------------------------
# Allocator
# ---------------------------------------------------------------------------

def test_allocator_equal_weights():
    alloc = Allocator()
    weights = alloc.allocate(["BTCUSDT", "ETHUSDT", "BNBUSDT"])
    assert len(weights) == 3
    assert pytest.approx(sum(weights.values())) == 1.0
    for w in weights.values():
        assert pytest.approx(w) == 1 / 3


def test_allocator_empty():
    alloc = Allocator()
    weights = alloc.allocate([])
    assert weights == {"default": 1.0}


def test_allocator_none():
    alloc = Allocator()
    weights = alloc.allocate()
    assert weights == {"default": 1.0}


def test_allocator_single():
    alloc = Allocator()
    weights = alloc.allocate(["BTCUSDT"])
    assert weights == {"BTCUSDT": 1.0}
