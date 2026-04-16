import os


class RiskManager:
    """Evaluate trades against prop-firm risk rules before execution."""

    def __init__(self):
        self.max_position_size = float(
            os.getenv("MAX_POSITION_SIZE", "1.0")
        )
        self.max_daily_loss_pct = float(
            os.getenv("MAX_DAILY_LOSS_PCT", "5.0")
        )
        self.max_total_loss_pct = float(
            os.getenv("MAX_TOTAL_LOSS_PCT", "10.0")
        )
        self.allowed_symbols = os.getenv(
            "ALLOWED_SYMBOLS", "EURUSD,GBPUSD,XAUUSD"
        ).split(",")

        self.daily_loss = 0.0

    def evaluate(self, symbol: str, side: str, volume: float) -> bool:
        """Return True if the trade passes all risk checks."""
        if symbol not in self.allowed_symbols:
            return False

        if volume > self.max_position_size:
            return False

        if side not in ("BUY", "SELL"):
            return False

        return True

    def record_loss(self, amount: float) -> None:
        """Track realised losses against daily limits."""
        self.daily_loss += amount

    def is_daily_limit_breached(self, account_balance: float) -> bool:
        """Check whether the daily loss limit has been exceeded."""
        if account_balance <= 0:
            return True
        pct = self.daily_loss / account_balance * 100
        return pct > self.max_daily_loss_pct

    def reset_daily(self) -> None:
        """Reset daily loss counter (call at start of each trading day)."""
        self.daily_loss = 0.0
