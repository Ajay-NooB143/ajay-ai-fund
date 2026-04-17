import os

import psycopg2


def get_connection():
    """Return a new database connection using DATABASE_URL."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable must be set")
    return psycopg2.connect(url)


def log_trade(symbol, side, qty, price):
    """Insert a trade record into the trades table."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO trades (symbol, side, qty, price)
            VALUES (%s, %s, %s, %s)
            """,
            (symbol, side, qty, price),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()
