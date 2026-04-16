class RiskManager:
    def check(self, signal, portfolio_value):
        """Basic risk check before executing a trade."""
        if portfolio_value <= 0:
            return "HOLD"
        return signal
