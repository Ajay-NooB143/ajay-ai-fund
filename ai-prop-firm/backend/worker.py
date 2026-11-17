"""Signals-only worker.

Consumes legacy queued messages only to quarantine/report them. It never
forwards messages to a broker or invokes an execution adapter.
"""
import time
import traceback

from trade_queue import TradeQueue

trade_queue = TradeQueue()


def run_worker() -> None:
    print("[worker] signals-only quarantine worker started")
    while True:
        try:
            signal = trade_queue.dequeue()
            if signal is None:
                continue
            # Do not log full payloads: they may contain private metadata.
            print("[worker] blocked queued trade: signals_only_mode")
        except Exception:
            traceback.print_exc()
            time.sleep(1)


if __name__ == "__main__":
    run_worker()
