"""Runner for the multi-pair trading strategy.

Executes one cycle of :func:`strategies.multi_pair.run_multi` every minute.
Run directly with ``python run_multi.py``.
"""

import time

from strategies.multi_pair import run_multi

if __name__ == "__main__":
    print("🚀 MULTI-PAIR BOT RUNNING")
    while True:
        run_multi()
        time.sleep(60)  # every 1 min
