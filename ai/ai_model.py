import random

# Fraction of valid signals rejected to avoid over-trading.
# Replace with a trained model threshold once XGBoost is wired in.
REJECTION_THRESHOLD = 0.3


def ai_decision(signal: str) -> str:
    """Filter an incoming signal with a simple probabilistic gate.

    Roughly ``REJECTION_THRESHOLD`` of valid signals are suppressed to avoid
    over-trading.  Replace the random logic with a trained XGBoost model (see
    ``ai/xgb_model.py``) when real features are available.

    Parameters
    ----------
    signal:
        Raw signal string, e.g. ``"BUY"`` or ``"SELL"``.

    Returns
    -------
    str
        The original *signal* if it passes the gate, otherwise ``"HOLD"``.
    """
    if signal not in ("BUY", "SELL"):
        return "HOLD"

    if random.random() > REJECTION_THRESHOLD:
        return signal

    return "HOLD"
