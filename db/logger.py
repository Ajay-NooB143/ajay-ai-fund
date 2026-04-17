import logging
import os

import psycopg2

logger = logging.getLogger(__name__)


def _get_connection():
    """Create and return a new database connection."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return psycopg2.connect(database_url)


def log_trade(
    symbol: str, side: str, qty: float, price: float
) -> None:
    """Insert a trade record into the trades table.

    Args:
        symbol: Trading pair symbol (e.g. 'BTCUSDT').
        side: Trade side ('BUY' or 'SELL').
        qty: Quantity traded.
        price: Execution price.
    """
    conn = None
    try:
        conn = _get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO trades (symbol, side, qty, price)
                VALUES (%s, %s, %s, %s)
                """,
                (symbol, side, qty, price),
            )
        conn.commit()
    except psycopg2.Error as exc:
        logger.error(
            "Failed to log trade: %s %s %s @ %s: %s",
            symbol, side, qty, price, exc,
        )
        if conn is not None:
            try:
                conn.rollback()
            except psycopg2.Error:
                logger.debug("Rollback failed", exc_info=True)
        raise
    finally:
        if conn is not None:
            conn.close()
