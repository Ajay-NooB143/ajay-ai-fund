"""Tests for the webhook endpoint and supporting modules."""


def test_ai_decision_passes_valid_signals():
    """ai_decision should return BUY or SELL (or HOLD) for valid inputs."""
    from ai.ai_model import ai_decision

    for _ in range(50):
        result = ai_decision("BUY")
        assert result in ("BUY", "HOLD")

    for _ in range(50):
        result = ai_decision("SELL")
        assert result in ("SELL", "HOLD")


def test_ai_decision_rejects_unknown_signal():
    """ai_decision should always return HOLD for unrecognised signals."""
    from ai.ai_model import ai_decision

    assert ai_decision("UNKNOWN") == "HOLD"
    assert ai_decision("") == "HOLD"
    assert ai_decision(None) == "HOLD"


def test_risk_check_default_passes():
    """risk_check should return True when no loss has accumulated."""
    from app.risk import reset_loss, risk_check

    reset_loss()
    assert risk_check() is True


def test_risk_check_blocks_after_limit():
    """risk_check should return False once the daily loss limit is exceeded."""
    from app.risk import reset_loss, risk_check, update_loss

    reset_loss()
    update_loss(-5.0)  # exceeds the 3 % limit
    assert risk_check() is False


def test_update_and_reset_loss():
    """update_loss and reset_loss should mutate and clear the loss counter."""
    from app.risk import reset_loss, risk_check, update_loss

    reset_loss()
    update_loss(-1.0)
    assert risk_check() is True  # still within limit

    update_loss(-3.0)
    assert risk_check() is False  # now over limit

    reset_loss()
    assert risk_check() is True  # reset clears the counter


def test_send_msg_missing_env(monkeypatch):
    """send_msg should not raise when env vars are absent."""
    monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    from services.telegram_bot import send_msg

    # Should complete without raising
    send_msg("test message")


def test_webhook_module_importable():
    """Verify the modules introduced by the webhook feature can be imported
    independently (without optional heavy deps such as psycopg2 / binance)."""
    from ai.ai_model import ai_decision  # noqa: F401
    from app.risk import reset_loss, risk_check, update_loss  # noqa: F401
    from services.telegram_bot import send_msg  # noqa: F401

    assert callable(ai_decision)
    assert callable(risk_check)
    assert callable(send_msg)


def test_project_structure_webhook():
    """Verify new files exist on disk."""
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    assert (root / "app" / "main.py").exists()
    assert (root / "ai" / "ai_model.py").exists()
    assert (root / "services" / "telegram_bot.py").exists()
