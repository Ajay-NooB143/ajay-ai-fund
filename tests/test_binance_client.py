"""Tests for agents/trading/binance_client.py helpers."""

import importlib
import sys
from unittest.mock import MagicMock, patch

MOCK_BALANCES = [
    {"asset": "BTC", "free": "0.5", "locked": "0.0"},
    {"asset": "ETH", "free": "2.0", "locked": "0.0"},
    {"asset": "USDT", "free": "0.0", "locked": "0.0"},
    {"asset": "BNB", "free": "0.0", "locked": "1.0"},
]

MODULE = "agents.trading.binance_client"


def _load_module_with_mock_client(balances=None):
    """Import (or reload) the binance_client module with a mocked Client class.

    Patching ``binance.client.Client`` prevents any real network call that
    would otherwise occur at module-load time when the module-level
    ``client = Client(...)`` runs.
    """
    mock_instance = MagicMock()
    mock_instance.get_account.return_value = {"balances": balances or MOCK_BALANCES}

    mock_class = MagicMock(return_value=mock_instance)

    # Evict any previously cached version so the patch takes effect cleanly.
    sys.modules.pop(MODULE, None)

    with patch("binance.client.Client", mock_class):
        module = importlib.import_module(MODULE)
        # Keep the patched client active for the caller via module attribute.
        module.client = mock_instance

    return module


def test_get_non_zero_balances_filters_correctly():
    """Only assets with free > 0 should be returned."""
    mod = _load_module_with_mock_client()
    result = mod.get_non_zero_balances()

    assets = [entry["asset"] for entry in result]
    assert "BTC" in assets
    assert "ETH" in assets
    assert "USDT" not in assets
    assert "BNB" not in assets


def test_get_non_zero_balances_empty_when_all_zero():
    """An account with all zero balances should return an empty list."""
    zero_balances = [{"asset": "XRP", "free": "0.0", "locked": "0.0"}]
    mod = _load_module_with_mock_client(zero_balances)
    assert mod.get_non_zero_balances() == []


def test_get_non_zero_balances_returns_empty_on_api_error():
    """A failed API call should return an empty list without raising."""
    mod = _load_module_with_mock_client()
    mod.client.get_account.side_effect = Exception("API error")
    assert mod.get_non_zero_balances() == []


def test_get_non_zero_balances_returns_empty_on_missing_balances_key():
    """A response missing the 'balances' key should return an empty list."""
    mod = _load_module_with_mock_client()
    mod.client.get_account.return_value = {}  # no 'balances' key
    assert mod.get_non_zero_balances() == []
