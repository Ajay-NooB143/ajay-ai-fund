"""Regression tests: MT5 adapter must remain signals-only."""
import importlib
import os
import sys


def _load_executor():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), os.pardir, "ai-prop-firm", "backend"
    ))
    if path not in sys.path:
        sys.path.insert(0, path)
    sys.modules.pop("mt5_executor", None)
    return importlib.import_module("mt5_executor").MT5Executor


def test_execute_is_always_blocked(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "false")
    executor = _load_executor()()
    result = executor.execute("XAUUSD", "BUY", 0.1)
    assert result == {"status": "blocked", "reason": "signals_only_mode"}
    assert executor.connected is False


def test_hedge_and_smart_execution_are_blocked():
    executor = _load_executor()()
    assert executor.hedge_trade("XAUUSD", 0.1)["status"] == "blocked"
    assert executor.smart_execution("BUY", 99, "XAUUSD", 0.1)["status"] == "blocked"
    assert executor.run_hedge_flow()["status"] == "blocked"


def test_lot_calculation_rejects_invalid_inputs():
    executor = _load_executor()()
    for args in [(0, 1, 10), (100, 0, 10), (100, 1, 0), (100, float("nan"), 10)]:
        try:
            executor.calc_lot(*args)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid risk input was accepted")


def test_lot_calculation_never_suggests_execution_size():
    executor = _load_executor()()
    assert executor.calc_lot(10_000, 1, 100) == 0.0
