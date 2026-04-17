"""Tests for MT5 hedge-mode execution.

These tests run without a live MT5 terminal by exercising the
``MT5Executor`` class in dry-run mode and the standalone functional
helpers with ``mt5`` mocked to ``None``.
"""

import importlib
import sys


# ------------------------------------------------------------------
# MT5Executor (dry-run mode)
# ------------------------------------------------------------------


def _load_executor():
    """Import MT5Executor even if MetaTrader5 is not installed."""
    # Ensure the ai-prop-firm package path is importable.
    import os
    firm_path = os.path.join(
        os.path.dirname(__file__), os.pardir, "ai-prop-firm", "backend",
    )
    abs_path = os.path.abspath(firm_path)
    if abs_path not in sys.path:
        sys.path.insert(0, abs_path)

    mod = importlib.import_module("mt5_executor")
    return mod.MT5Executor


def test_executor_dry_run_single_trade():
    MT5Executor = _load_executor()
    ex = MT5Executor()
    assert ex.dry_run is True

    result = ex.execute("XAUUSD", "BUY", 0.10)
    assert result["status"] == "dry_run"
    assert result["side"] == "BUY"
    assert result["volume"] == 0.10


def test_executor_dry_run_hedge():
    MT5Executor = _load_executor()
    ex = MT5Executor()

    result = ex.hedge_trade("XAUUSD", 0.05)
    assert "buy" in result and "sell" in result
    assert result["buy"]["status"] == "dry_run"
    assert result["sell"]["status"] == "dry_run"
    assert result["buy"]["side"] == "BUY"
    assert result["sell"]["side"] == "SELL"


def test_executor_smart_execution_high_confidence():
    MT5Executor = _load_executor()
    ex = MT5Executor()

    result = ex.smart_execution("BUY", 90, "XAUUSD", 0.1)
    assert result["status"] == "dry_run"
    assert result["side"] == "BUY"


def test_executor_smart_execution_medium_confidence():
    MT5Executor = _load_executor()
    ex = MT5Executor()

    result = ex.smart_execution("SELL", 70, "XAUUSD", 0.1)
    assert result["status"] == "dry_run"
    assert result["side"] == "SELL"


def test_executor_smart_execution_low_confidence_triggers_hedge():
    MT5Executor = _load_executor()
    ex = MT5Executor()

    result = ex.smart_execution("BUY", 50, "XAUUSD", 0.1)
    # Low confidence → hedge → dict with buy & sell keys
    assert "buy" in result and "sell" in result


def test_executor_calc_lot_basic():
    MT5Executor = _load_executor()
    ex = MT5Executor()

    # 10 000 balance, 1% risk, 100-point SL → risk_amount=100, lot=1.0
    lot = ex.calc_lot(10_000, 1.0, 100.0)
    assert lot == 1.0


def test_executor_calc_lot_minimum():
    MT5Executor = _load_executor()
    ex = MT5Executor()

    # Very small balance → should return minimum lot 0.01
    lot = ex.calc_lot(1, 0.01, 100.0)
    assert lot == 0.01


def test_executor_calc_lot_zero_sl():
    MT5Executor = _load_executor()
    ex = MT5Executor()

    lot = ex.calc_lot(10_000, 1.0, 0.0)
    assert lot == 0.01


def test_executor_run_hedge_flow():
    MT5Executor = _load_executor()
    ex = MT5Executor()

    out = ex.run_hedge_flow(
        symbol="XAUUSD", risk_pct=1.0, sl_points=100.0,
        signal="BUY", confidence=50.0,
    )
    assert "balance" in out
    assert "lot" in out
    assert "result" in out
    # Low confidence triggers hedge
    assert "buy" in out["result"] and "sell" in out["result"]


# ------------------------------------------------------------------
# Standalone functional module (execution/mt5_hedge.py)
# ------------------------------------------------------------------


def test_standalone_calc_lot():
    from execution.mt5_hedge import calc_lot_mt5

    assert calc_lot_mt5(10_000, 1.0, 100.0) == 1.0
    assert calc_lot_mt5(10_000, 1.0, 0.0) == 0.01
    assert calc_lot_mt5(1, 0.01, 100.0) == 0.01


def test_standalone_place_order_no_mt5():
    from execution.mt5_hedge import place_order

    result = place_order("XAUUSD", 0.1, "BUY")
    assert result["status"] == "error"


def test_standalone_hedge_trade_no_mt5():
    from execution.mt5_hedge import hedge_trade

    result = hedge_trade("XAUUSD", 0.1)
    assert "buy" in result and "sell" in result


def test_standalone_smart_execution_high():
    from execution.mt5_hedge import smart_execution

    result = smart_execution("BUY", 90, "XAUUSD", 0.1)
    # Without MT5 installed → error, but shape is correct
    assert "status" in result


def test_standalone_smart_execution_low():
    from execution.mt5_hedge import smart_execution

    result = smart_execution("BUY", 40, "XAUUSD", 0.1)
    # Low confidence → hedge dict
    assert "buy" in result and "sell" in result
