def calculate_pnl(entry, exit_price, side):
    """Return the profit/loss for a trade.

    Parameters
    ----------
    entry : float
        Entry price.
    exit_price : float
        Exit price.
    side : str
        ``"BUY"`` or ``"SELL"``.
    """
    if side == "BUY":
        return exit_price - entry
    else:
        return entry - exit_price
