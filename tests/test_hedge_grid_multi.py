"""Tests for the new hedge exit, grid-hedge, and multi-account modules.

All tests run without a live MT5 terminal by using the ``mt5 = None``
fallback paths that the production code already supports.
"""

from types import SimpleNamespace


# ===================================================================
# close_position & get_open_positions  (critical fix)
# ===================================================================

def test_close_position_no_mt5():
    """close_position gracefully returns an error when MT5 is unavailable."""
    from execution.mt5_hedge import close_position

    fake_pos = SimpleNamespace(type=0, symbol="XAUUSD", volume=0.1, ticket=1)
    result = close_position(fake_pos)
    assert result["status"] == "error"


def test_get_open_positions_no_mt5():
    """get_open_positions returns an empty list when MT5 is unavailable."""
    from execution.mt5_hedge import get_open_positions

    assert get_open_positions() == []
    assert get_open_positions("XAUUSD") == []


# ===================================================================
# Hedge Exit Manager
# ===================================================================

def _make_positions(buy_specs, sell_specs):
    """Create fake position objects for testing.

    *buy_specs* / *sell_specs* are lists of ``(volume, profit)`` tuples.
    """
    positions = []
    ticket = 1
    for vol, profit in buy_specs:
        positions.append(SimpleNamespace(
            type=0, symbol="XAUUSD", volume=vol, profit=profit,
            ticket=ticket, magic=999999,
        ))
        ticket += 1
    for vol, profit in sell_specs:
        positions.append(SimpleNamespace(
            type=1, symbol="XAUUSD", volume=vol, profit=profit,
            ticket=ticket, magic=999999,
        ))
        ticket += 1
    return positions


def test_calculate_floating_pnl():
    from execution.hedge_exit_manager import calculate_floating_pnl

    positions = _make_positions([(0.1, 5.0)], [(0.1, -3.0)])
    assert calculate_floating_pnl(positions) == 2.0


def test_detect_imbalance_balanced():
    from execution.hedge_exit_manager import detect_imbalance

    positions = _make_positions([(0.1, 0)], [(0.1, 0)])
    assert detect_imbalance(positions) is False


def test_detect_imbalance_one_side_only():
    from execution.hedge_exit_manager import detect_imbalance

    positions = _make_positions([(0.1, 0)], [])
    assert detect_imbalance(positions) is True


def test_detect_imbalance_ratio_exceeded():
    from execution.hedge_exit_manager import detect_imbalance

    # buy volume = 0.4, sell volume = 0.1 → ratio 4.0 → imbalanced (threshold=3.0)
    positions = _make_positions([(0.4, 0)], [(0.1, 0)])
    assert detect_imbalance(positions, ratio=3.0) is True


def test_detect_imbalance_empty():
    from execution.hedge_exit_manager import detect_imbalance

    assert detect_imbalance([]) is False


def test_evaluate_hedge_exit_no_positions():
    from execution.hedge_exit_manager import evaluate_hedge_exit

    result = evaluate_hedge_exit([])
    assert result["should_exit"] is False
    assert result["reason"] == "no_positions"


def test_evaluate_hedge_exit_profit_target():
    from execution.hedge_exit_manager import evaluate_hedge_exit

    positions = _make_positions([(0.1, 15.0)], [(0.1, -2.0)])
    result = evaluate_hedge_exit(positions, profit_target=10.0)
    assert result["should_exit"] is True
    assert result["reason"] == "profit_target"
    assert result["pnl"] == 13.0


def test_evaluate_hedge_exit_imbalance():
    from execution.hedge_exit_manager import evaluate_hedge_exit

    # Only one side → imbalanced → should exit
    positions = _make_positions([(0.1, 2.0)], [])
    result = evaluate_hedge_exit(positions, profit_target=100.0)
    assert result["should_exit"] is True
    assert result["reason"] == "imbalance"


def test_evaluate_hedge_exit_within_limits():
    from execution.hedge_exit_manager import evaluate_hedge_exit

    positions = _make_positions([(0.1, 1.0)], [(0.1, -0.5)])
    result = evaluate_hedge_exit(positions, profit_target=100.0)
    assert result["should_exit"] is False
    assert result["reason"] == "within_limits"


def test_close_all_hedge_positions_no_mt5():
    from execution.hedge_exit_manager import close_all_hedge_positions

    positions = _make_positions([(0.1, 5.0)], [(0.1, -3.0)])
    results = close_all_hedge_positions(positions)
    assert len(results) == 2
    # Without MT5 each close returns an error
    for r in results:
        assert r["status"] == "error"


def test_run_hedge_exit_check_no_mt5():
    from execution.hedge_exit_manager import run_hedge_exit_check

    # No MT5 → no positions → hold
    result = run_hedge_exit_check()
    assert result["action"] == "hold"
    assert result["closed"] == []


# ===================================================================
# Grid + Hedge Combo
# ===================================================================

def test_calculate_grid_levels_default():
    from execution.grid_hedge import calculate_grid_levels

    levels = calculate_grid_levels(2000.0, levels=2, spacing=50.0)
    assert levels == [1900.0, 1950.0, 2000.0, 2050.0, 2100.0]


def test_calculate_grid_levels_single():
    from execution.grid_hedge import calculate_grid_levels

    levels = calculate_grid_levels(100.0, levels=0, spacing=10.0)
    assert levels == [100.0]


def test_execute_grid_hedge_no_mt5():
    from execution.grid_hedge import execute_grid_hedge

    results = execute_grid_hedge("XAUUSD", 2000.0, lot=0.01, levels=1, spacing=50)
    # levels=1 → 3 grid prices (−1, 0, +1)
    assert len(results) == 3
    for entry in results:
        assert "level_price" in entry
        assert "result" in entry
        # Each result is a hedge dict with buy/sell
        assert "buy" in entry["result"] and "sell" in entry["result"]


def test_execute_grid_directional_no_mt5():
    from execution.grid_hedge import execute_grid_directional

    results = execute_grid_directional("XAUUSD", 2000.0, "BUY", lot=0.01, levels=1, spacing=50)
    assert len(results) == 3
    for entry in results:
        assert "level_price" in entry
        # Single direction → direct order result (not a hedge dict)
        assert "status" in entry["result"]


# ===================================================================
# Multi-Account System
# ===================================================================

def test_load_accounts_from_env_empty(monkeypatch):
    from execution.multi_account import load_accounts_from_env

    monkeypatch.delenv("MT5_ACCOUNTS", raising=False)
    monkeypatch.delenv("MT5_LOGIN", raising=False)
    monkeypatch.delenv("MT5_PASSWORD", raising=False)
    monkeypatch.delenv("MT5_SERVER", raising=False)

    assert load_accounts_from_env() == []


def test_load_accounts_from_env_single(monkeypatch):
    from execution.multi_account import load_accounts_from_env

    monkeypatch.delenv("MT5_ACCOUNTS", raising=False)
    monkeypatch.setenv("MT5_LOGIN", "12345")
    monkeypatch.setenv("MT5_PASSWORD", "pw")
    monkeypatch.setenv("MT5_SERVER", "Broker-S1")

    accounts = load_accounts_from_env()
    assert len(accounts) == 1
    assert accounts[0]["login"] == 12345
    assert accounts[0]["password"] == "pw"
    assert accounts[0]["server"] == "Broker-S1"


def test_load_accounts_from_env_multi(monkeypatch):
    from execution.multi_account import load_accounts_from_env

    monkeypatch.setenv("MT5_ACCOUNTS", "111:pw1:S1;222:pw2:S2")
    accounts = load_accounts_from_env()
    assert len(accounts) == 2
    assert accounts[0]["login"] == 111
    assert accounts[1]["login"] == 222


def test_execute_on_accounts_no_mt5():
    from execution.multi_account import execute_on_accounts

    accounts = [{"login": 111, "password": "pw", "server": "S1"}]
    results = execute_on_accounts(accounts, "XAUUSD", 0.1, "BUY")
    assert len(results) == 1
    assert results[0]["status"] == "error"
    assert results[0]["login"] == 111


def test_smart_execute_on_accounts_no_mt5():
    from execution.multi_account import smart_execute_on_accounts

    accounts = [{"login": 222, "password": "pw", "server": "S1"}]
    results = smart_execute_on_accounts(accounts, "BUY", 90.0, "XAUUSD", 0.1)
    assert len(results) == 1
    assert results[0]["login"] == 222


def test_run_multi_account_no_accounts(monkeypatch):
    from execution.multi_account import run_multi_account

    monkeypatch.delenv("MT5_ACCOUNTS", raising=False)
    monkeypatch.delenv("MT5_LOGIN", raising=False)
    monkeypatch.delenv("MT5_PASSWORD", raising=False)
    monkeypatch.delenv("MT5_SERVER", raising=False)

    results = run_multi_account()
    assert results == []
