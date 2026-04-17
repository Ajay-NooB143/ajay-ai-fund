"""Risk calculator: position sizing, stop-loss, take-profit, and R:R validation."""


def calculate_position_size(
    balance: float,
    risk_percent: float,
    entry_price: float,
    stop_loss_price: float,
) -> dict:
    """
    Calculate safe position size based on account risk.

    Parameters
    ----------
    balance        : Total account balance in quote currency.
    risk_percent   : Percentage of balance to risk on this trade.
    entry_price    : Planned entry price.
    stop_loss_price: Stop-loss price.

    Returns
    -------
    dict with position_size (base units), risk_amount, and stop_distance_pct.
    """
    if entry_price <= 0 or stop_loss_price <= 0:
        return {"error": "Prices must be positive"}
    if entry_price == stop_loss_price:
        return {"error": "entry_price and stop_loss_price must differ"}

    risk_amount = balance * (risk_percent / 100.0)
    stop_distance = abs(entry_price - stop_loss_price)
    stop_distance_pct = stop_distance / entry_price * 100.0
    position_size = risk_amount / stop_distance

    return {
        "position_size": round(position_size, 6),
        "risk_amount": round(risk_amount, 4),
        "stop_distance_pct": round(stop_distance_pct, 4),
    }


def calculate_take_profit(
    entry_price: float,
    stop_loss_price: float,
    reward_ratio: float = 2.0,
    side: str = "BUY",
) -> dict:
    """
    Calculate take-profit level for a given reward-to-risk ratio.

    Parameters
    ----------
    entry_price     : Entry price.
    stop_loss_price : Stop-loss price.
    reward_ratio    : Desired R:R multiplier (default 2.0).
    side            : 'BUY' (long) or 'SELL' (short).

    Returns
    -------
    dict with take_profit_price and risk_reward_ratio.
    """
    if entry_price <= 0 or stop_loss_price <= 0:
        return {"error": "Prices must be positive"}

    risk = abs(entry_price - stop_loss_price)
    if side.upper() == "BUY":
        take_profit = entry_price + risk * reward_ratio
    else:
        take_profit = entry_price - risk * reward_ratio

    return {
        "take_profit_price": round(take_profit, 6),
        "risk_reward_ratio": round(reward_ratio, 2),
    }


def full_trade_plan(
    balance: float,
    risk_percent: float,
    entry_price: float,
    stop_loss_price: float,
    reward_ratio: float = 2.0,
    side: str = "BUY",
) -> dict:
    """
    Return a complete trade plan combining position size and take-profit.

    Returns
    -------
    Merged dict with position_size, risk_amount, stop_distance_pct,
    take_profit_price, and risk_reward_ratio.
    """
    sizing = calculate_position_size(balance, risk_percent, entry_price, stop_loss_price)
    if "error" in sizing:
        return sizing

    tp = calculate_take_profit(entry_price, stop_loss_price, reward_ratio, side)
    if "error" in tp:
        return tp

    return {**sizing, **tp, "entry_price": entry_price, "stop_loss_price": stop_loss_price}


def calc_lot(balance: float, risk_pct: float, sl_pips: float) -> float:
    """Calculate position lot size from a pip-value risk model.

    Parameters
    ----------
    balance  : Account balance in quote currency.
    risk_pct : Percentage of balance to risk (e.g. ``1`` for 1 %).
    sl_pips  : Stop-loss distance in pips.

    Returns
    -------
    float
        Lot size rounded to three decimal places, or ``0.0`` when *sl_pips*
        is zero to avoid a division-by-zero error.
    """
    if sl_pips <= 0:
        return 0.0
    risk_amount = balance * (risk_pct / 100.0)
    lot = risk_amount / sl_pips
    return round(lot, 3)
