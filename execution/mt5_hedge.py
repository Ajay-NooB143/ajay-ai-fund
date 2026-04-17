"""Standalone MT5 hedge-mode execution module.

Provides functional helpers for hedge trading that can be used
independently of the ``MT5Executor`` class.  Every function gracefully
degrades when the ``MetaTrader5`` package is not installed (e.g. in CI).
"""

import os

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

# Unique identifier attached to every order for tracking.
HEDGE_MAGIC = 999999


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def mt5_connect(login: int = 0, password: str = "", server: str = "") -> bool:
    """Initialise and log in to the MT5 terminal.

    Credentials can be passed directly or read from the environment
    variables ``MT5_LOGIN``, ``MT5_PASSWORD``, and ``MT5_SERVER``.

    Returns ``True`` on success.
    """
    if mt5 is None:
        print("[mt5_hedge] MetaTrader5 package not available")
        return False

    if not mt5.initialize():
        print("[mt5_hedge] MT5 init failed")
        return False

    login = login or int(os.getenv("MT5_LOGIN", "0"))
    password = password or os.getenv("MT5_PASSWORD", "")
    server = server or os.getenv("MT5_SERVER", "")

    if login and password and server:
        authorised = mt5.login(login=login, password=password, server=server)
        if not authorised:
            print("[mt5_hedge] MT5 login failed")
            return False

    print("✅ MT5 Connected")
    return True


# ---------------------------------------------------------------------------
# Lot sizing
# ---------------------------------------------------------------------------

def calc_lot_mt5(balance: float, risk_pct: float, sl_points: float,
                 symbol: str = "XAUUSD") -> float:
    """Calculate lot size using MT5 tick-value data.

    Falls back to a simple risk/pip model when tick-value data is
    unavailable.

    Returns a minimum of ``0.01``.
    """
    if sl_points <= 0:
        return 0.01

    risk_amount = balance * (risk_pct / 100.0)

    tick_value = 0.0
    if mt5 is not None:
        info = mt5.symbol_info(symbol)
        if info is not None:
            tick_value = info.trade_tick_value

    if tick_value > 0:
        lot = risk_amount / (sl_points * tick_value)
    else:
        lot = risk_amount / sl_points

    return max(round(lot, 2), 0.01)


# ---------------------------------------------------------------------------
# Order placement
# ---------------------------------------------------------------------------

def place_order(symbol: str, lot: float, order_type: str) -> dict:
    """Place a single market order on MT5.

    Parameters
    ----------
    symbol     : Trading symbol (e.g. ``"XAUUSD"``).
    lot        : Trade volume.
    order_type : ``"BUY"`` or ``"SELL"``.

    Returns
    -------
    dict with the order result or an error description.
    """
    if mt5 is None:
        return {"status": "error", "reason": "MetaTrader5 not available"}

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return {"status": "error", "reason": f"No tick data for {symbol}"}

    price = tick.ask if order_type == "BUY" else tick.bid

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL,
        "price": price,
        "deviation": 10,
        "magic": HEDGE_MAGIC,
        "comment": "AI HEDGE",
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


# ---------------------------------------------------------------------------
# Hedge execution
# ---------------------------------------------------------------------------

def hedge_trade(symbol: str, lot: float) -> dict:
    """Execute a hedge: simultaneous BUY and SELL at the same volume.

    Returns a dict containing both order results.
    """
    print("⚡ Executing HEDGE mode")
    buy_order = place_order(symbol, lot, "BUY")
    sell_order = place_order(symbol, lot, "SELL")
    return {"buy": buy_order, "sell": sell_order}


# ---------------------------------------------------------------------------
# Smart (AI-driven) execution
# ---------------------------------------------------------------------------

def smart_execution(signal: str, confidence: float, symbol: str,
                    lot: float) -> dict:
    """Route to a single trade or hedge based on AI confidence.

    * confidence > 80  → single high-confidence trade
    * 60 < confidence <= 80  → single medium-confidence trade
    * confidence <= 60 → hedge (buy + sell)
    """
    if confidence > 60:
        return place_order(symbol, lot, signal)
    return hedge_trade(symbol, lot)


# ---------------------------------------------------------------------------
# Full flow
# ---------------------------------------------------------------------------

def run_mt5(symbol: str = "XAUUSD", risk_pct: float = 1.0,
            sl_points: float = 100.0, signal: str = "BUY",
            confidence: float = 55.0) -> dict | None:
    """End-to-end MT5 hedge-aware execution.

    Connects to MT5, reads the live account balance, calculates the
    lot size, and routes through :func:`smart_execution`.
    """
    if not mt5_connect():
        return None

    acct = mt5.account_info()
    balance = acct.balance if acct else 10_000.0

    lot = calc_lot_mt5(balance, risk_pct, sl_points, symbol)
    result = smart_execution(signal, confidence, symbol, lot)

    print("Trade Result:", result)
    return result
