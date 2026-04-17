"""Auto Hedge Exit Manager.

Tracks all open hedge positions, calculates total floating PnL, and
closes the hedge when:

* A configurable profit target is reached.
* One side of the hedge dominates (imbalance ratio exceeded).

This prevents endless hedge locks and margin drain.
"""

from __future__ import annotations

from execution.mt5_hedge import close_position, get_open_positions

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

# ---------------------------------------------------------------------------
# Default thresholds — callers may override via function arguments.
# ---------------------------------------------------------------------------

DEFAULT_PROFIT_TARGET = 10.0   # USD — close hedge once floating PnL >= target
DEFAULT_IMBALANCE_RATIO = 3.0  # close when one side's volume is ≥ 3× the other


# ---------------------------------------------------------------------------
# Position analysis helpers
# ---------------------------------------------------------------------------

def _split_positions(positions: list) -> tuple[list, list]:
    """Split *positions* into (buy_positions, sell_positions).

    MT5 position type ``0`` → BUY, ``1`` → SELL.
    """
    buys = [p for p in positions if p.type == 0]
    sells = [p for p in positions if p.type == 1]
    return buys, sells


def calculate_floating_pnl(positions: list) -> float:
    """Sum the unrealised profit across all *positions*.

    Each MT5 position object exposes a ``.profit`` attribute that
    represents the current floating PnL in the account currency.
    """
    return sum(p.profit for p in positions)


def detect_imbalance(positions: list,
                     ratio: float = DEFAULT_IMBALANCE_RATIO) -> bool:
    """Return ``True`` when one side's total volume exceeds the other by
    more than *ratio*.

    If only one side has positions the hedge is completely imbalanced.
    """
    buys, sells = _split_positions(positions)
    buy_vol = sum(p.volume for p in buys)
    sell_vol = sum(p.volume for p in sells)

    if buy_vol == 0 and sell_vol == 0:
        return False
    if buy_vol == 0 or sell_vol == 0:
        return True

    larger = max(buy_vol, sell_vol)
    smaller = min(buy_vol, sell_vol)
    return (larger / smaller) >= ratio


# ---------------------------------------------------------------------------
# Core exit logic
# ---------------------------------------------------------------------------

def evaluate_hedge_exit(
    positions: list,
    profit_target: float = DEFAULT_PROFIT_TARGET,
    imbalance_ratio: float = DEFAULT_IMBALANCE_RATIO,
) -> dict:
    """Decide whether the hedge should be closed.

    Returns
    -------
    dict
        ``{"should_exit": bool, "reason": str, "pnl": float}``
    """
    if not positions:
        return {"should_exit": False, "reason": "no_positions", "pnl": 0.0}

    pnl = calculate_floating_pnl(positions)

    if pnl >= profit_target:
        return {"should_exit": True, "reason": "profit_target", "pnl": pnl}

    if detect_imbalance(positions, imbalance_ratio):
        return {"should_exit": True, "reason": "imbalance", "pnl": pnl}

    return {"should_exit": False, "reason": "within_limits", "pnl": pnl}


def close_all_hedge_positions(positions: list) -> list[dict]:
    """Close every position in *positions* and return the results."""
    results: list[dict] = []
    for pos in positions:
        result = close_position(pos)
        results.append(result)
    return results


# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------

def run_hedge_exit_check(
    symbol: str | None = None,
    profit_target: float = DEFAULT_PROFIT_TARGET,
    imbalance_ratio: float = DEFAULT_IMBALANCE_RATIO,
) -> dict:
    """Check open hedge positions and close them if exit criteria are met.

    Parameters
    ----------
    symbol : str, optional
        Restrict to a single symbol (e.g. ``"XAUUSD"``).
    profit_target : float
        Close when floating PnL >= this amount (account currency).
    imbalance_ratio : float
        Close when one side's volume exceeds the other by this factor.

    Returns
    -------
    dict
        ``{"action": str, "reason": str, "pnl": float, "closed": list}``
    """
    positions = get_open_positions(symbol)
    evaluation = evaluate_hedge_exit(positions, profit_target, imbalance_ratio)

    if evaluation["should_exit"]:
        closed = close_all_hedge_positions(positions)
        return {
            "action": "closed",
            "reason": evaluation["reason"],
            "pnl": evaluation["pnl"],
            "closed": closed,
        }

    return {
        "action": "hold",
        "reason": evaluation["reason"],
        "pnl": evaluation["pnl"],
        "closed": [],
    }
