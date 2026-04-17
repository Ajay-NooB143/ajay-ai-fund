"""Multi-Account MT5 Execution System.

Executes the same trade across multiple MT5 accounts — suitable for
prop-firm scaling, fund management, or signal copying.

Accounts are configured as a list of credential dicts::

    ACCOUNTS = [
        {"login": 12345, "password": "pw1", "server": "Broker-Server1"},
        {"login": 67890, "password": "pw2", "server": "Broker-Server2"},
    ]

Each account is connected to in turn, the trade is placed, and then
the terminal is shut down before moving to the next account (MT5 only
supports a single active connection at a time).
"""

from __future__ import annotations

import os

from execution.mt5_hedge import (
    calc_lot_mt5,
    place_order,
    smart_execution,
)

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None


# ---------------------------------------------------------------------------
# Account configuration helpers
# ---------------------------------------------------------------------------

def load_accounts_from_env() -> list[dict]:
    """Build an account list from environment variables.

    Expects ``MT5_ACCOUNTS`` as a semicolon-separated list of
    ``login:password:server`` triples, e.g.::

        MT5_ACCOUNTS="12345:pw1:Broker-S1;67890:pw2:Broker-S2"

    Falls back to the single-account ``MT5_LOGIN`` / ``MT5_PASSWORD`` /
    ``MT5_SERVER`` variables when ``MT5_ACCOUNTS`` is not set.
    """
    raw = os.getenv("MT5_ACCOUNTS", "")
    if raw:
        accounts: list[dict] = []
        for entry in raw.split(";"):
            parts = entry.strip().split(":")
            if len(parts) >= 3:
                accounts.append({
                    "login": int(parts[0]),
                    "password": parts[1],
                    "server": ":".join(parts[2:]),  # server may contain ':'
                })
        if accounts:
            return accounts

    # Fallback: single-account env vars.
    login = os.getenv("MT5_LOGIN", "0")
    password = os.getenv("MT5_PASSWORD", "")
    server = os.getenv("MT5_SERVER", "")
    if login != "0" and password and server:
        return [{"login": int(login), "password": password, "server": server}]

    return []


# ---------------------------------------------------------------------------
# Per-account connection
# ---------------------------------------------------------------------------

def _connect_account(account: dict) -> bool:
    """Initialise MT5 and log in with the given *account* credentials.

    Returns ``True`` on success.
    """
    if mt5 is None:
        return False

    if not mt5.initialize():
        print(f"[multi] MT5 init failed for login {account.get('login')}")
        return False

    authorised = mt5.login(
        login=account["login"],
        password=account["password"],
        server=account["server"],
    )
    if not authorised:
        print(f"[multi] Login failed for {account['login']}")
        mt5.shutdown()
        return False

    return True


def _disconnect() -> None:
    """Shut down the MT5 terminal connection."""
    if mt5 is not None:
        mt5.shutdown()


# ---------------------------------------------------------------------------
# Multi-account execution
# ---------------------------------------------------------------------------

def execute_on_accounts(
    accounts: list[dict],
    symbol: str,
    lot: float,
    order_type: str,
) -> list[dict]:
    """Place the same order on every account in *accounts*.

    Parameters
    ----------
    accounts : list[dict]
        Each dict must have ``login``, ``password``, ``server`` keys.
    symbol : str
        Trading symbol (e.g. ``"XAUUSD"``).
    lot : float
        Volume to trade on each account.
    order_type : str
        ``"BUY"`` or ``"SELL"``.

    Returns
    -------
    list[dict]
        One result per account with the login and order outcome.
    """
    results: list[dict] = []

    for acct in accounts:
        login = acct.get("login", 0)

        if not _connect_account(acct):
            results.append({
                "login": login,
                "status": "error",
                "reason": "connection_failed",
            })
            continue

        try:
            result = place_order(symbol, lot, order_type)
            result["login"] = login
            results.append(result)
        finally:
            _disconnect()

    return results


def smart_execute_on_accounts(
    accounts: list[dict],
    signal: str,
    confidence: float,
    symbol: str,
    lot: float,
) -> list[dict]:
    """Run :func:`smart_execution` on every account.

    Routes to a single trade or a hedge depending on *confidence*.
    """
    results: list[dict] = []

    for acct in accounts:
        login = acct.get("login", 0)

        if not _connect_account(acct):
            results.append({
                "login": login,
                "status": "error",
                "reason": "connection_failed",
            })
            continue

        try:
            result = smart_execution(signal, confidence, symbol, lot)
            if isinstance(result, dict) and "buy" not in result:
                result["login"] = login
            else:
                result = {"login": login, "trade": result}
            results.append(result)
        finally:
            _disconnect()

    return results


# ---------------------------------------------------------------------------
# Convenience: full flow for all configured accounts
# ---------------------------------------------------------------------------

def run_multi_account(
    symbol: str = "XAUUSD",
    risk_pct: float = 1.0,
    sl_points: float = 100.0,
    signal: str = "BUY",
    confidence: float = 55.0,
    accounts: list[dict] | None = None,
) -> list[dict]:
    """End-to-end multi-account execution.

    Reads accounts from the environment when *accounts* is not provided.
    For each account: connect → read balance → calc lot → execute → disconnect.

    Returns a list of per-account result dicts.
    """
    if accounts is None:
        accounts = load_accounts_from_env()

    if not accounts:
        print("[multi] No accounts configured")
        return []

    results: list[dict] = []

    for acct in accounts:
        login = acct.get("login", 0)

        if not _connect_account(acct):
            results.append({
                "login": login,
                "status": "error",
                "reason": "connection_failed",
            })
            continue

        try:
            acct_info = mt5.account_info()
            balance = acct_info.balance if acct_info else 10_000.0

            lot = calc_lot_mt5(balance, risk_pct, sl_points, symbol)
            result = smart_execution(signal, confidence, symbol, lot)

            entry = {"login": login, "balance": balance, "lot": lot, "result": result}
            results.append(entry)
            print(f"[multi] Account {login}: {result}")
        finally:
            _disconnect()

    return results
