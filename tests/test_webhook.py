"""Tests for the webhook endpoint and supporting modules."""
import importlib
import sys
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stub_heavy_deps():
    """Insert lightweight stubs for deps not available in all environments."""
    for mod in ("psycopg2", "binance", "binance.client"):
        if mod not in sys.modules:
            sys.modules[mod] = MagicMock()


def _reload_webhook():
    """Return a freshly imported (or reloaded) app.main module."""
    _stub_heavy_deps()
    sys.modules.pop("app.main", None)
    import app.main as webhook_main
    importlib.reload(webhook_main)
    return webhook_main


# ---------------------------------------------------------------------------
# ai_decision
# ---------------------------------------------------------------------------

def test_ai_decision_passes_valid_signals():
    """ai_decision should return BUY or SELL (or HOLD) for valid inputs."""
    from ai.ai_model import ai_decision

    for _ in range(50):
        assert ai_decision("BUY") in ("BUY", "HOLD")
    for _ in range(50):
        assert ai_decision("SELL") in ("SELL", "HOLD")


def test_ai_decision_rejects_unknown_signal():
    """ai_decision should always return HOLD for unrecognised signals."""
    from ai.ai_model import ai_decision

    assert ai_decision("UNKNOWN") == "HOLD"
    assert ai_decision("") == "HOLD"
    assert ai_decision(None) == "HOLD"


# ---------------------------------------------------------------------------
# risk
# ---------------------------------------------------------------------------

def test_risk_check_default_passes():
    """risk_check should return True when no loss has accumulated."""
    from app.risk import reset_loss, risk_check

    reset_loss()
    assert risk_check() is True


def test_risk_check_blocks_after_limit():
    """risk_check should return False once the daily loss limit is exceeded."""
    from app.risk import reset_loss, risk_check, update_loss

    reset_loss()
    update_loss(-5.0)
    assert risk_check() is False


def test_update_and_reset_loss():
    """update_loss and reset_loss should mutate and clear the loss counter."""
    from app.risk import reset_loss, risk_check, update_loss

    reset_loss()
    update_loss(-1.0)
    assert risk_check() is True

    update_loss(-3.0)
    assert risk_check() is False

    reset_loss()
    assert risk_check() is True


# ---------------------------------------------------------------------------
# telegram_bot
# ---------------------------------------------------------------------------

def test_send_msg_missing_env(monkeypatch):
    """send_msg should not raise when env vars are absent."""
    monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    from services.telegram_bot import send_msg

    send_msg("test message")


def test_send_msg_with_env(monkeypatch):
    """send_msg should POST to the Telegram API when env vars are set."""
    monkeypatch.setenv("TELEGRAM_TOKEN", "fake_token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("services.telegram_bot.requests.post", return_value=mock_response) as mock_post:
        from services import telegram_bot

        telegram_bot.send_msg("hello")
        mock_post.assert_called_once()
        assert "fake_token" in mock_post.call_args[0][0]
        mock_response.raise_for_status.assert_called_once()


# ---------------------------------------------------------------------------
# Webhook endpoint (FastAPI integration)
# ---------------------------------------------------------------------------

def test_webhook_returns_hold_for_filtered_signal(monkeypatch):
    """Webhook should return HOLD when ai_decision filters the signal."""
    from fastapi.testclient import TestClient

    monkeypatch.setattr("ai.ai_model.random.random", lambda: 0.0)

    webhook_main = _reload_webhook()
    client = TestClient(webhook_main.app)
    response = client.post("/webhook", json={"action": "BUY", "symbol": "BTCUSDT"})
    assert response.status_code == 200
    assert response.json()["status"] == "HOLD"


def test_webhook_blocked_by_risk(monkeypatch):
    """Webhook should return risk blocked when loss limit is exceeded."""
    from fastapi.testclient import TestClient

    monkeypatch.setattr("ai.ai_model.random.random", lambda: 1.0)

    from app.risk import reset_loss, update_loss

    reset_loss()  # ensure clean state before this test
    update_loss(-10.0)

    webhook_main = _reload_webhook()
    client = TestClient(webhook_main.app)
    response = client.post("/webhook", json={"action": "BUY", "symbol": "BTCUSDT"})
    assert response.status_code == 200
    assert response.json()["status"] == "risk blocked"

    reset_loss()  # restore clean state for subsequent tests


def test_webhook_executes_trade(monkeypatch):
    """Webhook should call execute_trade and send_msg when signal passes."""
    from fastapi.testclient import TestClient

    monkeypatch.setattr("ai.ai_model.random.random", lambda: 1.0)

    from app.risk import reset_loss

    reset_loss()

    webhook_main = _reload_webhook()

    with patch.object(webhook_main, "execute_trade", return_value="SAFE MODE") as mock_exec, \
            patch.object(webhook_main, "send_msg") as mock_notify:
        client = TestClient(webhook_main.app)
        response = client.post("/webhook", json={"action": "BUY", "symbol": "BTCUSDT"})

    assert response.status_code == 200
    assert response.json()["status"] == "SAFE MODE"
    mock_exec.assert_called_once_with("BTCUSDT", "BUY")
    mock_notify.assert_called_once_with("BUY BTCUSDT")


# ---------------------------------------------------------------------------
# Structural checks
# ---------------------------------------------------------------------------

def test_webhook_module_importable():
    """Light-weight modules can be imported without heavy external deps."""
    from ai.ai_model import ai_decision  # noqa: F401
    from app.risk import reset_loss, risk_check, update_loss  # noqa: F401
    from services.telegram_bot import send_msg  # noqa: F401

    assert callable(ai_decision)
    assert callable(risk_check)
    assert callable(send_msg)


def test_project_structure_webhook():
    """New files exist on disk."""
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    assert (root / "app" / "main.py").exists()
    assert (root / "ai" / "ai_model.py").exists()
    assert (root / "services" / "telegram_bot.py").exists()
