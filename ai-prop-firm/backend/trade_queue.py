import json
import os

import redis


class TradeQueue:
    """Redis-backed queue for trade signals awaiting execution."""

    QUEUE_KEY = "trade_queue"

    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True,
        )

    def enqueue(self, trade: dict) -> None:
        """Push a trade signal onto the queue."""
        self.client.rpush(self.QUEUE_KEY, json.dumps(trade))

    def dequeue(self) -> dict | None:
        """Pop the next trade signal from the queue (blocking)."""
        result = self.client.blpop(self.QUEUE_KEY, timeout=5)
        if result:
            _, payload = result
            return json.loads(payload)
        return None

    def size(self) -> int:
        """Return the current number of pending trades."""
        return self.client.llen(self.QUEUE_KEY)
