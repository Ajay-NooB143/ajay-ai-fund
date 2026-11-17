"""Conservative input and loss-limit checks for signal reporting only."""
import math
import os


class RiskManager:
    def __init__(self):
        self.max_position_size = float(os.getenv("MAX_POSITION_SIZE", "1.0"))
        self.max_daily_loss_pct = float(os.getenv("MAX_DAILY_LOSS_PCT", "5.0"))
        self.max_total_loss_pct = float(os.getenv("MAX_TOTAL_LOSS_PCT", "10.0"))
        self.allowed_symbols = {
            item.strip().upper()
            for item in os.getenv("ALLOWED_SYMBOLS", "XAUUSD.m,XAUUSD").split(",")
            if item.strip()
        }
        self.daily_loss = 0.0

    def evaluate(self, symbol: str, side: str, volume: float) -> bool:
        try:
            volume = float(volume)
            max_size = float(self.max_position_size)
        except (TypeError, ValueError):
            return False
        if not math.isfinite(volume) or not math.isfinite(max_size):
            return False
        if volume <= 0 or max_size <= 0 or volume > max_size:
            return False
        if not isinstance(symbol, str) or symbol.strip().upper() not in self.allowed_symbols:
            return False
        if side not in ("BUY", "SELL"):
            return False
        # Balance is not supplied here, so do not guess a denominator.\n        # Call is_daily_limit_breached(balance) at the account-aware layer.\n        return True

    def record_loss(self, amount: float) -> None:
        amount = float(amount)
        if not math.isfinite(amount) or amount < 0:
            raise ValueError("loss amount must be finite and non-negative")
        self.daily_loss += amount

    def is_daily_limit_breached(self, account_balance: float) -> bool:
        try:
            balance = float(account_balance)
        except (TypeError, ValueError):
            return True
        if not math.isfinite(balance) or balance <= 0:
            return True
        return self.daily_loss / balance * 100 >= self.max_daily_loss_pct

    def reset_daily(self) -> None:
        self.daily_loss = 0.0
