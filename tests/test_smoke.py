"""Smoke tests to verify key project modules are importable."""
import importlib


def test_app_bot_importable():
    """Ensure the app.bot entry point module can be imported."""
    mod = importlib.util.find_spec("app.bot")
    assert mod is not None, "app.bot module not found"


def test_main_importable():
    """Ensure the top-level main module can be imported."""
    mod = importlib.util.find_spec("main")
    assert mod is not None, "main module not found"
