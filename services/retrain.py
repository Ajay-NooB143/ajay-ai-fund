import time

from services.checkpointer_api import CheckpointerService

# Retrain interval: 1 week in seconds
RETRAINING_INTERVAL_SECONDS = 7 * 24 * 60 * 60


class RetrainService:
    def __init__(self):
        self.checkpointer = CheckpointerService()

    def run(self):
        while True:
            print("🔄 Retraining AI...")
            # After retraining, persist a checkpoint of the updated model
            # state so it can be restored later.
            self.checkpointer.save(
                "rl_agent",
                {"status": "retrained"},
                metadata={"trigger": "scheduled"},
            )
            print("✅ Checkpoint saved for rl_agent")
            time.sleep(RETRAINING_INTERVAL_SECONDS)
