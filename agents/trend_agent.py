class TrendAgent:
    """Follow the trend: buy when price is above EMA, sell otherwise."""

    def act(self, state: dict) -> str:
        return "BUY" if state["close"] > state["ema"] else "SELL"
