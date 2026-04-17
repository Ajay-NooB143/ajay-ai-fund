import threading

_MAX_DAILY_LOSS = 3.0  # percent
_current_loss: float = 0.0
_loss_lock = threading.Lock()


def risk_check() -> bool:
    """Return ``True`` when trading is still allowed, ``False`` when the daily
    loss limit has been breached.

    ``_current_loss`` is expected to be a negative number representing the
    cumulative percentage loss for the session (e.g. ``-3.5`` means 3.5 %
    drawdown).  External code should update ``update_loss()`` after each trade.
    Thread-safe: protected by ``_loss_lock``.
    """
    with _loss_lock:
        if _current_loss < -_MAX_DAILY_LOSS:
            print("❌ DAILY LOSS LIMIT HIT")
            return False
    return True


def update_loss(delta: float) -> None:
    """Accumulate *delta* (positive = gain, negative = loss) into the session
    loss tracker.  Call this after every completed trade.

    Thread-safe: protected by ``_loss_lock``.

    Parameters
    ----------
    delta:
        Change in portfolio value as a percentage (e.g. ``-1.5`` for a 1.5 %
        loss or ``+2.0`` for a 2 % gain).
    """
    global _current_loss
    with _loss_lock:
        _current_loss += delta


def reset_loss() -> None:
    """Reset the daily loss counter (e.g. at the start of a new trading day).

    Thread-safe: protected by ``_loss_lock``.
    """
    global _current_loss
    with _loss_lock:
        _current_loss = 0.0


class RiskManager:
    def check(self, signal, portfolio_value):
        """Basic risk check before executing a trade."""
        if portfolio_value <= 0:
            return "HOLD"
        return signal
