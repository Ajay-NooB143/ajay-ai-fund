class MeanAgent:
    """Mean-reversion agent: buy oversold, sell overbought via RSI."""

    _RSI_OVERSOLD = 30
    _RSI_OVERBOUGHT = 70

    def act(self, state: dict) -> str:
        if state["rsi"] < self._RSI_OVERSOLD:
            return "BUY"
        if state["rsi"] > self._RSI_OVERBOUGHT:
            return "SELL"
        return "HOLD"
