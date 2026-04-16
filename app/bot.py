import time

from ai.rl_agent import RLAgent
from ai.orderbook import predict_orderflow
from app.execution import execute_trade

TRADING_SYMBOL = "BTCUSDT"
TRADING_LOOP_INTERVAL_SECONDS = 10

rl = RLAgent()


def run_bot():
    print("🚀 BOT RUNNING")

    while True:
        symbol = TRADING_SYMBOL

        # TODO: replace placeholder observation with actual market state data
        rl_signal = rl.predict([0, 0, 0, 0, 0])
        # TODO: replace placeholder orderbook with actual Binance depth data
        ob_signal = predict_orderflow({
            "bids": [["0", "1"]],
            "asks": [["0", "1"]]
        })

        signal = rl_signal if rl_signal == ob_signal else "HOLD"

        if signal != "HOLD":
            execute_trade(symbol, signal)

        time.sleep(TRADING_LOOP_INTERVAL_SECONDS)
