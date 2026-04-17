import random


class ScalperAgent:
    """High-frequency scalper: randomly picks a direction (placeholder)."""

    def act(self, state: dict) -> str:  # noqa: ARG002
        return random.choice(["BUY", "SELL"])
