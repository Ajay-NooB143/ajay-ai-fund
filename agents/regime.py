REGIME_UPTREND = "UPTREND"
REGIME_DOWNTREND = "DOWNTREND"
REGIME_HIGH_VOL = "HIGH_VOL"
REGIME_RANGE = "RANGE"

_ADX_THRESHOLD = 25
_ATR_VOL_MULTIPLIER = 1.5


def detect_regime(state: dict) -> str:
    """Return the current market regime based on EMA trend, ADX and ATR.

    Parameters
    ----------
    state:
        Dictionary with keys ``ema``, ``ema_prev``, ``adx``, ``atr``,
        and ``atr_mean``.

    Returns
    -------
    str
        One of ``"UPTREND"``, ``"DOWNTREND"``, ``"HIGH_VOL"``, or
        ``"RANGE"``.
    """
    if state["ema"] > state["ema_prev"] and state["adx"] > _ADX_THRESHOLD:
        return REGIME_UPTREND

    if state["ema"] < state["ema_prev"] and state["adx"] > _ADX_THRESHOLD:
        return REGIME_DOWNTREND

    if state["atr"] > state["atr_mean"] * _ATR_VOL_MULTIPLIER:
        return REGIME_HIGH_VOL

    return REGIME_RANGE
