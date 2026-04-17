import sys
import threading

from app.bot import run_bot
from services.retrain import RetrainService


def run_conva():
    """Launch CONVA — the conversational AI interface."""
    from agents.conva import ConvaAgent

    agent = ConvaAgent()
    print("🤖 CONVA — Built for AI (type 'exit' to quit)\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCONVA: Goodbye!")
            break
        if user_input.lower() in ("exit", "quit", "bye"):
            print("CONVA: Goodbye!")
            break
        if not user_input:
            continue
        response = agent.chat(user_input)
        print(f"CONVA: {response}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "conva":
        run_conva()
    else:
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
