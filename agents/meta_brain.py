"""Meta-brain: regime-aware multi-agent ensemble decision engine."""

from agents.mean_agent import MeanAgent
from agents.regime import (
    REGIME_DOWNTREND,
    REGIME_RANGE,
    REGIME_UPTREND,
    detect_regime,
)
from agents.risk_agent import RiskAgent
from agents.scalper_agent import ScalperAgent
from agents.trend_agent import TrendAgent
from ai.rl_agent import RLAgent

_rl = RLAgent()


def _transformer_predict(state: dict) -> str:  # noqa: ARG001
    """Stub transformer signal — replace with a real model."""
    return _rl.predict(list(state.values()))


def compete(agents: dict, state: dict, next_price: float) -> tuple[str, dict]:
    """Score each agent by its simulated PnL and return the best performer.

    Parameters
    ----------
    agents:
        Mapping of agent name → agent instance (must have an ``act`` method).
    state:
        Current market state dictionary.
    next_price:
        Next bar's close price used to calculate simulated PnL.

    Returns
    -------
    tuple[str, dict]
        ``(best_agent_name, scores_dict)``
    """
    scores: dict[str, float] = {}
    price = state["close"]

    for name, agent in agents.items():
        action = agent.act(state)
        if action == "BUY":
            scores[name] = next_price - price
        elif action == "SELL":
            scores[name] = price - next_price
        else:
            scores[name] = 0.0

    best = max(scores, key=scores.get)
    return best, scores


def meta_brain(state: dict, next_price: float) -> str:
    """Combine regime detection, agent competition and AI ensemble into one signal.

    Decision logic:
    1. Detect market regime.
    2. Filter agents relevant to the regime.
    3. Run agent competition to find the best performer.
    4. Get transformer and RL signals.
    5. If transformer and RL agree, use their consensus.
    6. Otherwise fall back to the best regime-selected agent.

    Parameters
    ----------
    state:
        Current market state dictionary.
    next_price:
        Next bar's close price (used for competition scoring).

    Returns
    -------
    str
        ``"BUY"``, ``"SELL"``, or ``"HOLD"``
    """
    agents = {
        "trend": TrendAgent(),
        "mean": MeanAgent(),
        "scalp": ScalperAgent(),
        "risk": RiskAgent(),
    }

    regime = detect_regime(state)

    if regime in (REGIME_UPTREND, REGIME_DOWNTREND):
        chosen = ["trend"]
    elif regime == REGIME_RANGE:
        chosen = ["mean"]
    else:
        chosen = ["risk", "scalp"]

    filtered_agents = {k: agents[k] for k in chosen}

    best, _scores = compete(filtered_agents, state, next_price)

    t_pred = _transformer_predict(state)
    rl_pred = _rl.predict(list(state.values()))

    if t_pred == rl_pred:
        return t_pred

    return filtered_agents[best].act(state)
