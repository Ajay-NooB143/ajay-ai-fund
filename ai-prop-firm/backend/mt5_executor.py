"""Signals-only MT5 adapter.

Live order execution is intentionally disabled. This module preserves the
legacy class name for import compatibility but never connects to MT5.
"""
import math


class MT5Executor:
    """Compatibility adapter that rejects every execution request."""

    def __init__(self):
        self.dry_run = True
        self.connected = False

    def connect(self) -> bool:
        return False

    def execute(self, symbol: str, side: str, volume: float,
                price: float = 0.0, comment: str = "") -> dict:
        return {"status": "blocked", "reason": "signals_only_mode"}

    def calc_lot(self, balance: float, risk_pct: float, sl_points: float,
                 symbol: str = "XAUUSD") -> float:
        values = (balance, risk_pct, sl_points)
        if not all(math.isfinite(float(v)) for v in values):
            raise ValueError("risk inputs must be finite")
        if balance <= 0 or risk_pct <= 0 or sl_points <= 0:
            raise ValueError("balance, risk_pct and sl_points must be positive")
        return 0.0

    def hedge_trade(self, symbol: str, volume: float) -> dict:
        return {"status": "blocked", "reason": "signals_only_mode"}

    def smart_execution(self, signal: str, confidence: float,
                        symbol: str, volume: float) -> dict:
        return {"status": "blocked", "reason": "signals_only_mode"}

    def run_hedge_flow(self, **kwargs) -> dict:
        return {"status": "blocked", "reason": "signals_only_mode"}

    def shutdown(self) -> None:
        self.connected = False
