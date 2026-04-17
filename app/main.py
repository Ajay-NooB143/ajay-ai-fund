import os

from fastapi import FastAPI
from pydantic import BaseModel

from ai.ai_model import ai_decision
from app.execution import execute_trade
from app.risk import risk_check
from services.telegram_bot import send_msg

app = FastAPI(title="AI Fund Webhook", version="1.0.0")

# Read from the environment so it can be toggled at runtime without a redeploy.
BOT_ACTIVE = os.getenv("BOT_ACTIVE", "true").lower() not in ("false", "0", "no")


class WebhookRequest(BaseModel):
    symbol: str = "BTCUSDT"
    action: str
    price: float | None = None


@app.post("/webhook")
async def webhook(data: WebhookRequest):
    """Receive a TradingView (or similar) alert and act on it."""
    if not BOT_ACTIVE:
        return {"status": "bot stopped"}

    # AI decision layer
    decision = ai_decision(data.action)

    if decision == "HOLD":
        return {"status": "HOLD"}

    # Risk gate
    if not risk_check():
        return {"status": "risk blocked"}

    # Execute the trade
    result = execute_trade(data.symbol, decision)

    send_msg(f"{decision} {data.symbol}")

    return {"status": result}
