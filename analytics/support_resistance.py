"""Support / Resistance auto-detector using rolling pivot-point analysis."""

import numpy as np


def _pivot_highs(high: list, window: int = 5) -> list:
    """Return indices where price is a local pivot high."""
    highs = np.array(high, dtype=float)
    pivots = []
    for i in range(window, len(highs) - window):
        if highs[i] == max(highs[i - window: i + window + 1]):
            pivots.append(i)
    return pivots


def _pivot_lows(low: list, window: int = 5) -> list:
    """Return indices where price is a local pivot low."""
    lows = np.array(low, dtype=float)
    pivots = []
    for i in range(window, len(lows) - window):
        if lows[i] == min(lows[i - window: i + window + 1]):
            pivots.append(i)
    return pivots


def _cluster_levels(prices: list, tolerance_pct: float = 0.5) -> list:
    """
    Merge nearby price levels into clusters.

    Levels within *tolerance_pct* % of each other are averaged into one zone.
    """
    if not prices:
        return []
    sorted_prices = sorted(prices)
    clusters = [[sorted_prices[0]]]
    for price in sorted_prices[1:]:
        ref = np.mean(clusters[-1])
        if abs(price - ref) / ref * 100 <= tolerance_pct:
            clusters[-1].append(price)
        else:
            clusters.append([price])
    return [round(float(np.mean(c)), 6) for c in clusters]


def detect_support_resistance(
    high: list,
    low: list,
    close: list,
    window: int = 5,
    tolerance_pct: float = 0.5,
    max_levels: int = 5,
) -> dict:
    """
    Detect and auto-update support and resistance levels from OHLC data.

    The function identifies pivot highs (resistance candidates) and pivot
    lows (support candidates), clusters nearby levels, and returns the
    strongest zones sorted by proximity to the latest close price.

    Parameters
    ----------
    high / low / close : OHLC price lists (equal length).
    window             : Half-window size for pivot detection (default 5).
    tolerance_pct      : Price proximity % for merging levels (default 0.5 %).
    max_levels         : Maximum number of levels to return per side (default 5).

    Returns
    -------
    dict with:
        resistance_levels – list of resistance price levels (ascending)
        support_levels    – list of support price levels (descending)
        current_price     – latest close price
    """
    if not high or not low or not close:
        return {"error": "Price data is required"}
    if not (len(high) == len(low) == len(close)):
        return {"error": "high, low, close must have equal length"}

    current_price = float(close[-1])

    ph_indices = _pivot_highs(high, window)
    pl_indices = _pivot_lows(low, window)

    raw_resistance = [high[i] for i in ph_indices]
    raw_support = [low[i] for i in pl_indices]

    resistance_levels = _cluster_levels(raw_resistance, tolerance_pct)
    support_levels = _cluster_levels(raw_support, tolerance_pct)

    # Keep only levels above current price for resistance, below for support
    resistance_levels = sorted(
        [r for r in resistance_levels if r > current_price]
    )[:max_levels]
    support_levels = sorted(
        [s for s in support_levels if s < current_price], reverse=True
    )[:max_levels]

    return {
        "resistance_levels": resistance_levels,
        "support_levels": support_levels,
        "current_price": round(current_price, 6),
    }


def nearest_level(levels: list, price: float) -> float | None:
    """Return the level in *levels* closest to *price*, or None if empty."""
    if not levels:
        return None
    return min(levels, key=lambda lvl: abs(lvl - price))
