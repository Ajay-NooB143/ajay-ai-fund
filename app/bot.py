import time

from ai.rl_agent import RLAgent
from ai.orderbook import predict_orderflow
from app.execution import execute_trade

rl = RLAgent()


def run_bot():
    print("🚀 BOT RUNNING")

    while True:
        symbol = "BTCUSDT"

        rl_signal = rl.predict([0, 0, 0, 0, 0])
        ob_signal = predict_orderflow({
            "bids": [["0", "1"]],
            "asks": [["0", "1"]]
        })

        signal = rl_signal if rl_signal == ob_signal else "HOLD"

        if signal != "HOLD":
            execute_trade(symbol, signal)

        time.sleep(10)
