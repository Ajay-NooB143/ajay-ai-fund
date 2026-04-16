import threading

from app.bot import run_bot
from services.retrain import RetrainService

if __name__ == "__main__":
    print("💀 AI FUND STARTED")

    threading.Thread(target=run_bot).start()
    threading.Thread(target=RetrainService().run).start()
