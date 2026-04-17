"""Tests for strategies.multi_pair."""

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# get_signal
# ---------------------------------------------------------------------------

def test_get_signal_returns_valid_value():
    from strategies.multi_pair import get_signal

    for _ in range(100):
        sig = get_signal("BTCUSDT")
        assert sig in ("BUY", "SELL", "HOLD")


# ---------------------------------------------------------------------------
# position_size
# ---------------------------------------------------------------------------

def test_position_size_one_percent_risk():
    from strategies.multi_pair import NOTIONAL_DIVISOR, RISK_PERCENT, position_size

    assert position_size(10_000) == round((10_000 * RISK_PERCENT) / NOTIONAL_DIVISOR, 5)
    assert position_size(0) == 0.0


# ---------------------------------------------------------------------------
# get_balance
# ---------------------------------------------------------------------------

def test_get_balance_returns_usdt_free():
    mock_client = MagicMock()
    mock_client.get_account.return_value = {
        "balances": [
            {"asset": "BTC", "free": "0.5"},
            {"asset": "USDT", "free": "1234.56"},
        ]
    }
    with patch("strategies.multi_pair._get_client", return_value=mock_client):
        from strategies.multi_pair import get_balance

        assert get_balance() == pytest.approx(1234.56)


def test_get_balance_missing_usdt():
    mock_client = MagicMock()
    mock_client.get_account.return_value = {"balances": [{"asset": "BTC", "free": "1"}]}
    with patch("strategies.multi_pair._get_client", return_value=mock_client):
        from strategies.multi_pair import get_balance

        assert get_balance() == 0.0


# ---------------------------------------------------------------------------
# execute — SAFE_MODE
# ---------------------------------------------------------------------------

def test_execute_safe_mode(capsys):
    import strategies.multi_pair as mp

    original = mp.SAFE_MODE
    mp.SAFE_MODE = True
    try:
        result = mp.execute("BTCUSDT", "BUY", 0.001)
        assert result is not None
        assert result["status"] == "SIMULATED"
        assert result["symbol"] == "BTCUSDT"
        captured = capsys.readouterr()
        assert "[SAFE]" in captured.out
    finally:
        mp.SAFE_MODE = original


# ---------------------------------------------------------------------------
# run_multi
# ---------------------------------------------------------------------------

def test_run_multi_respects_max_trades():
    """run_multi should never execute more than MAX_TRADES orders."""
    import strategies.multi_pair as mp

    original_safe = mp.SAFE_MODE
    mp.SAFE_MODE = True
    try:
        with patch("strategies.multi_pair.get_balance", return_value=10_000.0):
            with patch("strategies.multi_pair.get_signal", return_value="BUY"):
                count = mp.run_multi()
                assert count <= mp.MAX_TRADES
    finally:
        mp.SAFE_MODE = original_safe


def test_run_multi_skips_hold():
    """run_multi should not execute any trades when all signals are HOLD."""
    import strategies.multi_pair as mp

    original_safe = mp.SAFE_MODE
    mp.SAFE_MODE = True
    try:
        with patch("strategies.multi_pair.get_balance", return_value=10_000.0):
            with patch("strategies.multi_pair.get_signal", return_value="HOLD"):
                count = mp.run_multi()
                assert count == 0
    finally:
        mp.SAFE_MODE = original_safe
