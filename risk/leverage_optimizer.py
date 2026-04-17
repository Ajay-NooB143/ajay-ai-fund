"""Leverage optimizer: suggests the optimal leverage given volatility and risk parameters."""

import numpy as np


def calculate_atr(high: list, low: list, close: list, period: int = 14) -> float:
    """Calculate Average True Range (ATR) as a volatility measure."""
    if len(high) < 2 or len(low) < 2 or len(close) < 2:
        return 0.0

    true_ranges = []
    for i in range(1, len(close)):
        tr = max(
            high[i] - low[i],
            abs(high[i] - close[i - 1]),
            abs(low[i] - close[i - 1]),
        )
        true_ranges.append(tr)

    if not true_ranges:
        return 0.0

    recent = true_ranges[-period:] if len(true_ranges) >= period else true_ranges
    return float(np.mean(recent))


def optimize_leverage(
    balance: float,
    entry_price: float,
    stop_loss_price: float,
    max_risk_percent: float = 1.0,
    max_leverage: int = 20,
    high: list = None,
    low: list = None,
    close: list = None,
    atr_period: int = 14,
) -> dict:
    """
    Suggest the optimal leverage to use for a trade.

    Parameters
    ----------
    balance          : Account balance in quote currency.
    entry_price      : Planned entry price.
    stop_loss_price  : Hard stop-loss price.
    max_risk_percent : Maximum account percentage to risk per trade (default 1 %).
    max_leverage     : Platform cap on leverage (default 20x).
    high / low / close : OHLC lists used to compute ATR-based volatility adjustment.
    atr_period       : Lookback window for ATR (default 14).

    Returns
    -------
    dict with keys:
        suggested_leverage  – recommended leverage (1 – max_leverage)
        position_size       – position size in base currency
        risk_amount         – dollar amount at risk
        atr                 – ATR value used (0 if not provided)
        volatility_factor   – scaling factor derived from ATR (1.0 = neutral)
    """
    if entry_price <= 0 or stop_loss_price <= 0:
        return {"error": "entry_price and stop_loss_price must be positive"}
    if entry_price == stop_loss_price:
        return {"error": "entry_price and stop_loss_price must differ"}

    risk_amount = balance * (max_risk_percent / 100.0)
    stop_distance_pct = abs(entry_price - stop_loss_price) / entry_price

    # Base leverage: use enough leverage so that the stop-loss distance equals the risk %
    if stop_distance_pct == 0:
        return {"error": "stop_distance_pct is zero"}
    base_leverage = (max_risk_percent / 100.0) / stop_distance_pct

    # Volatility adjustment: reduce leverage when ATR is elevated
    atr = 0.0
    volatility_factor = 1.0
    if high and low and close and len(close) > 1:
        atr = calculate_atr(high, low, close, atr_period)
        avg_price = float(np.mean(close))
        if avg_price > 0:
            atr_pct = atr / avg_price
            # Scale down leverage when ATR % is high (> 1 % is considered volatile)
            volatility_factor = max(0.25, min(1.0, 0.01 / atr_pct)) if atr_pct > 0 else 1.0

    suggested_leverage = base_leverage * volatility_factor
    suggested_leverage = max(1, min(max_leverage, round(suggested_leverage)))

    position_value = (balance * suggested_leverage)
    position_size = position_value / entry_price

    return {
        "suggested_leverage": int(suggested_leverage),
        "position_size": round(position_size, 6),
        "risk_amount": round(risk_amount, 4),
        "atr": round(atr, 6),
        "volatility_factor": round(volatility_factor, 4),
    }
