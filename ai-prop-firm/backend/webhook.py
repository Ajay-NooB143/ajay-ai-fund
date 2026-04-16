import hmac
import hashlib
import os

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel

from risk import RiskManager
from trade_queue import TradeQueue

router = APIRouter()
risk_manager = RiskManager()
trade_queue = TradeQueue()

API_SECRET = os.getenv("API_SECRET", "change-me-in-production")


class TradeSignal(BaseModel):
    symbol: str
    side: str  # "BUY" or "SELL"
    volume: float
    price: float = 0.0
    comment: str = ""


@router.post("/signal")
async def receive_signal(
    signal: TradeSignal,
    request: Request,
    x_signature: str = Header(default=""),
):
    """Receive a trading signal from an external source (e.g., TradingView)."""
    body = await request.body()
    expected_sig = hmac.new(
        API_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()

    if x_signature and not hmac.compare_digest(x_signature, expected_sig):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Run risk checks before queuing the trade
    approved = risk_manager.evaluate(
        symbol=signal.symbol,
        side=signal.side,
        volume=signal.volume,
    )

    if not approved:
        return {"status": "rejected", "reason": "Risk check failed"}

    # Enqueue trade for async execution
    trade_queue.enqueue(signal.model_dump())
    return {"status": "queued", "signal": signal.model_dump()}
