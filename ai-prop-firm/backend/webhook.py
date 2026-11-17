"""Authenticated, signals-only webhook. No execution queue is used."""
import hashlib
import hmac
import math
import os

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from risk import RiskManager

router = APIRouter()
risk_manager = RiskManager()


class TradeSignal(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    side: str
    volume: float = Field(gt=0, allow_inf_nan=False)
    price: float = Field(default=0.0, ge=0, allow_inf_nan=False)
    comment: str = Field(default="", max_length=256)


@router.post("/signal")
async def receive_signal(
    signal: TradeSignal,
    request: Request,
    x_signature: str = Header(default=""),
):
    secret = os.getenv("API_SECRET", "")
    if not secret or secret == "change-me-in-production":
        raise HTTPException(status_code=503, detail="Webhook authentication is not configured")

    body = await request.body()
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not x_signature or not hmac.compare_digest(x_signature, expected):
        raise HTTPException(status_code=401, detail="Invalid signature")

    if not math.isfinite(signal.volume) or not math.isfinite(signal.price):
        raise HTTPException(status_code=422, detail="Non-finite numeric input")

    if signal.side not in ("BUY", "SELL"):
        raise HTTPException(status_code=422, detail="side must be BUY or SELL")

    if not risk_manager.evaluate(signal.symbol, signal.side, signal.volume):
        return {"status": "rejected", "reason": "risk_check_failed"}

    # Deliberately return a signal only. Never enqueue an executable order.
    return {
        "status": "signal_accepted",
        "execution": "disabled",
        "signal": signal.model_dump(),
    }
