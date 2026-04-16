import threading

from app.bot import run_bot
from services.retrain import RetrainService

if __name__ == "__main__":
    print("💀 AI FUND STARTED")

    threading.Thread(target=run_bot, daemon=True).start()
    threading.Thread(target=RetrainService().run, daemon=True).start()

    # Keep main thread alive
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("💀 AI FUND STOPPED")
