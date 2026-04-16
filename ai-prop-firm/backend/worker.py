"""Background worker that consumes trades from the Redis queue and
forwards them to the MT5 executor."""

import time
import traceback

from trade_queue import TradeQueue
from mt5_executor import MT5Executor

trade_queue = TradeQueue()
executor = MT5Executor()


def run_worker() -> None:
    """Continuously pull trades from the queue and execute them."""
    print("[worker] Trade worker started")
    while True:
        try:
            trade = trade_queue.dequeue()
            if trade is None:
                continue

            print(f"[worker] Processing trade: {trade}")
            result = executor.execute(
                symbol=trade["symbol"],
                side=trade["side"],
                volume=trade["volume"],
                price=trade.get("price", 0.0),
                comment=trade.get("comment", ""),
            )
            print(f"[worker] Result: {result}")
        except Exception:
            traceback.print_exc()
            time.sleep(1)


if __name__ == "__main__":
    run_worker()
