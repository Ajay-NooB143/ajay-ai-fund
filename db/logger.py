import os
import time

import psycopg2

# Number of retry attempts for transient connection failures.
MAX_RETRIES = 3
# Base delay (in seconds) between retries; doubled on each attempt.
RETRY_DELAY = 2


def get_connection():
    """Return a new database connection using ``DATABASE_URL``.

    Retries up to :data:`MAX_RETRIES` times with exponential back-off when
    the connection is refused (e.g. PostgreSQL is still starting up).

    Raises
    ------
    RuntimeError
        If ``DATABASE_URL`` is not set.
    psycopg2.OperationalError
        If the connection cannot be established after all retries.
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable must be set")

    delay = RETRY_DELAY
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return psycopg2.connect(url)
        except psycopg2.OperationalError:
            if attempt == MAX_RETRIES:
                raise
            print(
                f"[DB] Connection attempt {attempt}/{MAX_RETRIES} failed, "
                f"retrying in {delay}s…"
            )
            time.sleep(delay)
            delay *= 2
    # Unreachable, but keeps type-checkers happy.
    raise psycopg2.OperationalError("Unable to connect after retries")


def log_trade(symbol, side, qty, price):
    """Insert a trade record into the ``trades`` table.

    If the database is unreachable the error is printed but **not**
    re-raised so that the calling code (e.g. the trading bot) can
    continue operating.
    """
    try:
        conn = get_connection()
    except Exception as exc:
        print(f"[DB] Could not connect – trade not logged: {exc}")
        return

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
    except Exception as exc:
        print(f"[DB] Failed to log trade: {exc}")
    finally:
        conn.close()
