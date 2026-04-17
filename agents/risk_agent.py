class RiskAgent:
    """Defensive agent that always holds, preventing any trade."""

    def act(self, state: dict) -> str:  # noqa: ARG002
        return "HOLD"
