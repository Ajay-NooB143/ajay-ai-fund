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

    # ------------------------------------------------------------------
    # Hedge-mode helpers
    # ------------------------------------------------------------------

    def calc_lot(
        self,
        balance: float,
        risk_pct: float,
        sl_points: float,
        symbol: str = "XAUUSD",
    ) -> float:
        """Calculate lot size using MT5 tick-value data.

        Falls back to a simple risk/pip model when MT5 tick-value data is
        unavailable (e.g. in dry-run or CI environments).

        Parameters
        ----------
        balance   : Account balance.
        risk_pct  : Percentage of balance to risk.
        sl_points : Stop-loss distance in points.
        symbol    : Trading symbol (default ``XAUUSD``).

        Returns
        -------
        float – lot size rounded to two decimal places, minimum ``0.01``.
        """
        if sl_points <= 0:
            return 0.01

        risk_amount = balance * (risk_pct / 100.0)

        tick_value = 0.0
        if mt5 is not None and self.connected:
            info = mt5.symbol_info(symbol)
            if info is not None:
                tick_value = info.trade_tick_value

        if tick_value > 0:
            lot = risk_amount / (sl_points * tick_value)
        else:
            lot = risk_amount / sl_points

        return max(round(lot, 2), 0.01)

    def hedge_trade(self, symbol: str, volume: float) -> dict:
        """Open simultaneous BUY and SELL positions (hedge mode).

        Parameters
        ----------
        symbol : Trading symbol.
        volume : Lot size for each leg.

        Returns
        -------
        dict with ``buy`` and ``sell`` execution results.
        """
        buy_result = self.execute(symbol, "BUY", volume, comment="AI HEDGE BUY")
        sell_result = self.execute(symbol, "SELL", volume, comment="AI HEDGE SELL")
        return {"buy": buy_result, "sell": sell_result}

    def smart_execution(
        self,
        signal: str,
        confidence: float,
        symbol: str,
        volume: float,
    ) -> dict:
        """AI-driven execution: single trade when confident, hedge when not.

        Parameters
        ----------
        signal     : ``"BUY"`` or ``"SELL"``.
        confidence : Model confidence percentage (0-100).
        symbol     : Trading symbol.
        volume     : Lot size.

        Returns
        -------
        dict – execution result(s).
        """
        if confidence > 80:
            return self.execute(symbol, signal, volume, comment="AI HIGH-CONF")
        elif confidence > 60:
            return self.execute(symbol, signal, volume, comment="AI MED-CONF")
        else:
            return self.hedge_trade(symbol, volume)

    def run_hedge_flow(self, symbol: str = "XAUUSD", risk_pct: float = 1.0,
                       sl_points: float = 100.0, signal: str = "BUY",
                       confidence: float = 55.0) -> dict:
        """End-to-end hedge-aware execution flow.

        Connects to MT5, calculates lot size from the live account
        balance, and routes the trade through :meth:`smart_execution`.

        Parameters
        ----------
        symbol     : Trading symbol (default ``XAUUSD``).
        risk_pct   : Percentage of balance to risk.
        sl_points  : Stop-loss distance in points.
        signal     : ``"BUY"`` or ``"SELL"``.
        confidence : Model confidence (0-100).

        Returns
        -------
        dict with ``lot``, ``balance``, and ``result`` keys.
        """
        if not self.dry_run:
            if not self.connected and not self.connect():
                return {"status": "error", "reason": "MT5 connection failed"}

        # Obtain account balance (dry-run uses a default value).
        if self.dry_run or mt5 is None:
            balance = 10_000.0
        else:
            acct = mt5.account_info()
            balance = acct.balance if acct else 10_000.0

        lot = self.calc_lot(balance, risk_pct, sl_points, symbol)
        result = self.smart_execution(signal, confidence, symbol, lot)
        return {"balance": balance, "lot": lot, "result": result}

    def shutdown(self) -> None:
        """Cleanly disconnect from the MT5 terminal."""
        if mt5 is not None and self.connected:
            mt5.shutdown()
            self.connected = False
