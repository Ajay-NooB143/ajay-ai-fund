import os

from binance.client import Client

from db.logger import log_trade
from portfolio.portfolio_manager import get_live_balance
from risk.risk_calculator import calc_lot
from services.telegram_bot import send_msg

_client = None

SAFE_MODE = True

# Risk parameters read from environment variables with sensible defaults.
_RISK_PERCENT = float(os.getenv("RISK_PERCENT", "1"))    # % of balance per trade
_SL_PIPS = float(os.getenv("SL_PIPS", "50"))             # stop-loss distance in pips
# Minimum lot when calc_lot returns zero; configurable for different pairs.
_MIN_LOT = float(os.getenv("MIN_LOT", "0.001"))


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_SECRET") or os.getenv("BINANCE_API_SECRET")
        if not api_key or not api_secret:
            raise RuntimeError(
                "BINANCE_API_KEY and BINANCE_SECRET (or BINANCE_API_SECRET) "
                "environment variables must be set"
            )
        _client = Client(api_key, api_secret)
    return _client


def execute_trade(symbol, side, price: float = 0.0):
    """Execute a market order and send a Telegram trade alert.

    Parameters
    ----------
    symbol:
        Trading pair, e.g. ``"BTCUSDT"``.
    side:
        ``"BUY"`` or ``"SELL"``.
    price:
        Current market price used only for the notification message.
        When ``0.0`` the live ticker price is queried from Binance.
    """
    client = _get_client()

    if price <= 0.0:
        price = float(client.get_symbol_ticker(symbol=symbol)["price"])

    balance = get_live_balance()
    qty = calc_lot(balance, _RISK_PERCENT, _SL_PIPS)
    if qty <= 0:
        qty = _MIN_LOT

    order_summary: str = ""

    if SAFE_MODE:
        print(f"[SAFE] {side} {symbol} @ {price} | bal={balance} lot={qty}")
        order_summary = "SAFE_MODE"
    else:
        if side == "BUY":
            order_raw = client.order_market_buy(symbol=symbol, quantity=qty)
        else:
            order_raw = client.order_market_sell(symbol=symbol, quantity=qty)

        # Extract only essential fields to keep the Telegram message concise.
        order_summary = f"orderId={order_raw.get('orderId')} status={order_raw.get('status')}"

        try:
            log_trade(symbol, side, qty, price)
        except Exception as exc:
            print(f"[WARN] Failed to log trade: {exc}")

        print(f"EXECUTED {side} {symbol} @ {price}")

    msg = (
        f"🚀 AJAY AI FUND\n\n"
        f"📊 Symbol: {symbol}\n"
        f"💰 Balance: {balance} USDT\n"
        f"📉 Price: {price}\n\n"
        f"🤖 Signal: {side}\n\n"
        f"⚖️ Lot: {qty}\n\n"
        f"✅ Order: {order_summary}"
    )
    send_msg(msg)
