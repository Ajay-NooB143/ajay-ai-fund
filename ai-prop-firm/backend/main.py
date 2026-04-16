from fastapi import FastAPI
from webhook import router as webhook_router
from auth import router as auth_router

app = FastAPI(title="AI Prop Firm", version="1.0.0")

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(webhook_router, prefix="/webhook", tags=["webhook"])


@app.get("/")
def root():
    return {"status": "running", "service": "AI Prop Firm"}


@app.get("/health")
def health():
    return {"status": "healthy"}
