"""MetaTrader 5 trade executor.

Connects to an MT5 terminal and places market orders.  When the
``DRY_RUN`` environment variable is set to ``true`` (the default),
orders are logged but not actually sent to the broker.
"""

import os

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None  # Allow import on systems without MT5 (e.g. CI)


class MT5Executor:
    """Send trade orders to a MetaTrader 5 terminal."""

    def __init__(self):
        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
        self.connected = False

    def connect(self) -> bool:
        """Initialise the MT5 connection."""
        if mt5 is None:
            print("[mt5] MetaTrader5 package not available")
            return False

        if not mt5.initialize():
            print(f"[mt5] init failed: {mt5.last_error()}")
            return False

        self.connected = True
        print("[mt5] Connected to terminal")
        return True

    def execute(
        self,
        symbol: str,
        side: str,
        volume: float,
        price: float = 0.0,
        comment: str = "",
    ) -> dict:
        """Place a market order on MT5 (or simulate in dry-run mode)."""
        if self.dry_run:
            return {
                "status": "dry_run",
                "symbol": symbol,
                "side": side,
                "volume": volume,
            }

        if not self.connected and not self.connect():
            return {"status": "error", "reason": "MT5 connection failed"}

        if side == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
        else:
            order_type = mt5.ORDER_TYPE_SELL
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return {"status": "error", "reason": f"No tick data for {symbol}"}

        fill_price = tick.ask if side == "BUY" else tick.bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": fill_price,
            "deviation": 20,
            "magic": 100000,
            "comment": comment or "ai-prop-firm",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            error = result.comment if result else "unknown error"
            return {"status": "error", "reason": error}

        return {
            "status": "executed",
            "order": result.order,
            "price": result.price,
            "volume": result.volume,
        }

    def shutdown(self) -> None:
        """Cleanly disconnect from the MT5 terminal."""
        if mt5 is not None and self.connected:
            mt5.shutdown()
            self.connected = False
