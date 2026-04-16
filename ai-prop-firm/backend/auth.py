import os
import hashlib
import hmac

from fastapi import APIRouter, HTTPException, Header

router = APIRouter()

API_SECRET = os.getenv("API_SECRET", "change-me-in-production")


def verify_signature(payload: str, signature: str) -> bool:
    """Verify HMAC-SHA256 signature of incoming webhook payloads."""
    expected = hmac.new(
        API_SECRET.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/verify")
def verify_token(x_api_key: str = Header(...)):
    """Verify that the provided API key is valid."""
    if not hmac.compare_digest(x_api_key, API_SECRET):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"authenticated": True}
