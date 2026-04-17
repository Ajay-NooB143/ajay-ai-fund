"""Basic smoke tests for the project."""


def test_imports():
    """Verify that core application modules can be imported."""
    import app
    import app.bot
    import app.execution
    import app.risk
    import db
    import db.logger
    import db.pnl
    assert app is not None
    assert app.bot is not None
    assert app.execution is not None
    assert app.risk is not None
    assert db is not None
    assert db.logger is not None
    assert db.pnl is not None


def test_project_structure():
    """Verify key project files exist."""
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    assert (root / "main.py").exists()
    assert (root / "requirements.txt").exists()
    assert (root / "app" / "__init__.py").exists()
    assert (root / "db" / "__init__.py").exists()
    assert (root / "db" / "schema.sql").exists()


def test_calculate_pnl():
    """Verify PnL calculation for BUY and SELL sides."""
    from db.pnl import calculate_pnl

    assert calculate_pnl(100, 110, "BUY") == 10
    assert calculate_pnl(100, 90, "BUY") == -10
    assert calculate_pnl(110, 100, "SELL") == 10
    assert calculate_pnl(90, 100, "SELL") == -10
