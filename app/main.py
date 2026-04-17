from fastapi import FastAPI

from ai.ai_model import ai_decision
from app.execution import execute_trade
from app.risk import risk_check
from services.telegram_bot import send_msg

app = FastAPI(title="AI Fund Webhook", version="1.0.0")

BOT_ACTIVE = True


@app.post("/webhook")
async def webhook(data: dict):
    """Receive a TradingView (or similar) alert and act on it."""
    if not BOT_ACTIVE:
        return {"status": "bot stopped"}

    symbol = data.get("symbol", "BTCUSDT")
    signal = data.get("action")

    # AI decision layer
    decision = ai_decision(signal)

    if decision == "HOLD":
        return {"status": "HOLD"}

    # Risk gate
    if not risk_check():
        return {"status": "risk blocked"}

    # Execute the trade
    result = execute_trade(symbol, decision)

    send_msg(f"{decision} {symbol}")

    return {"status": result}
