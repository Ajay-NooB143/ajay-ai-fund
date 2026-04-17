"""Grid + Hedge Combo Strategy.

Provides layered entry execution where each grid level places both a BUY
and a SELL order.  This captures volatility in ranging markets and
survives fake breakouts.

Grid levels are spaced at a configurable interval (in price points)
above and below a base price.  At each level the module opens a
hedged pair (BUY + SELL) via :func:`execution.mt5_hedge.hedge_trade`.

Example with ``levels=3`` and ``spacing=50`` around base price 2 000::

    Level −3: 1 850  →  BUY + SELL
    Level −2: 1 900  →  BUY + SELL
    Level −1: 1 950  →  BUY + SELL
    Level  0: 2 000  →  BUY + SELL  (base)
    Level +1: 2 050  →  BUY + SELL
    Level +2: 2 100  →  BUY + SELL
    Level +3: 2 150  →  BUY + SELL
"""

from __future__ import annotations

from execution.mt5_hedge import hedge_trade, place_order

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

# ---------------------------------------------------------------------------
# Default grid parameters
# ---------------------------------------------------------------------------

DEFAULT_LEVELS = 3        # number of levels above AND below the base price
DEFAULT_SPACING = 50.0    # price-point distance between grid levels
DEFAULT_LOT = 0.01        # volume per leg


# ---------------------------------------------------------------------------
# Grid level calculation
# ---------------------------------------------------------------------------

def calculate_grid_levels(
    base_price: float,
    levels: int = DEFAULT_LEVELS,
    spacing: float = DEFAULT_SPACING,
) -> list[float]:
    """Return an ordered list of grid prices centred on *base_price*.

    The list includes ``2 * levels + 1`` entries (the base plus *levels*
    above and *levels* below).
    """
    grid: list[float] = []
    for i in range(-levels, levels + 1):
        grid.append(round(base_price + i * spacing, 5))
    return grid


# ---------------------------------------------------------------------------
# Grid execution
# ---------------------------------------------------------------------------

def execute_grid_hedge(
    symbol: str,
    base_price: float,
    lot: float = DEFAULT_LOT,
    levels: int = DEFAULT_LEVELS,
    spacing: float = DEFAULT_SPACING,
) -> list[dict]:
    """Place a hedge pair (BUY + SELL) at every grid level.

    Each level triggers :func:`hedge_trade` which opens simultaneous
    BUY and SELL positions at market price.  The *base_price* and
    *spacing* define logical entry levels — because MT5 market orders
    execute at the current price, the grid primarily controls **when**
    (at what price) the bot decides to add new layers.

    Parameters
    ----------
    symbol : str
        Trading symbol, e.g. ``"XAUUSD"``.
    base_price : float
        Centre of the grid (usually the current market price).
    lot : float
        Volume per leg at each level.
    levels : int
        Number of grid levels above **and** below *base_price*.
    spacing : float
        Distance in price points between levels.

    Returns
    -------
    list[dict]
        One result dict per grid level, each containing the level price
        and the hedge result (``buy`` / ``sell``).
    """
    grid_prices = calculate_grid_levels(base_price, levels, spacing)
    results: list[dict] = []

    for price in grid_prices:
        hedge_result = hedge_trade(symbol, lot)
        results.append({"level_price": price, "result": hedge_result})

    return results


def execute_grid_directional(
    symbol: str,
    base_price: float,
    side: str,
    lot: float = DEFAULT_LOT,
    levels: int = DEFAULT_LEVELS,
    spacing: float = DEFAULT_SPACING,
) -> list[dict]:
    """Place a single-direction order at every grid level.

    Use this when the AI signal is high-confidence and only one side
    should be entered at each level.

    Parameters
    ----------
    symbol : str
        Trading symbol.
    base_price : float
        Centre of the grid.
    side : str
        ``"BUY"`` or ``"SELL"``.
    lot : float
        Volume per order.
    levels : int
        Grid levels above and below *base_price*.
    spacing : float
        Distance between levels.

    Returns
    -------
    list[dict]
        One result dict per grid level.
    """
    grid_prices = calculate_grid_levels(base_price, levels, spacing)
    results: list[dict] = []

    for price in grid_prices:
        order_result = place_order(symbol, lot, side)
        results.append({"level_price": price, "result": order_result})

    return results
