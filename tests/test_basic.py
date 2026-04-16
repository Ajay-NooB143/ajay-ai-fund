"""Basic smoke tests for the project."""


def test_imports():
    """Verify that core application modules can be imported."""
    import app
    import app.bot
    import app.execution
    import app.risk
    assert app is not None


def test_project_structure():
    """Verify key project files exist."""
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    assert (root / "main.py").exists()
    assert (root / "requirements.txt").exists()
    assert (root / "app" / "__init__.py").exists()
