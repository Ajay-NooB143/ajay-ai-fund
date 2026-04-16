import time

# Retrain interval: 1 week in seconds
RETRAINING_INTERVAL_SECONDS = 7 * 24 * 60 * 60


class RetrainService:
    def run(self):
        while True:
            print("🔄 Retraining AI...")
            time.sleep(RETRAINING_INTERVAL_SECONDS)
