import random


def ai_decision(signal: str) -> str:
    """Filter an incoming signal with a simple probabilistic gate.

    A random threshold rejects roughly 30 % of signals to avoid over-trading.
    Replace the random logic with a trained XGBoost model (see
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

    if random.random() > 0.3:
        return signal

    return "HOLD"
