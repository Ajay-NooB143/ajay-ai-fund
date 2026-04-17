import random
import time

# =========================
# 🔐 SETTINGS
# =========================
LIVE_TRADING = False
MAX_RISK = 0.02

# =========================
# 🧠 STRATEGY WEIGHTS (Learning)
# =========================
strategy_weights = {
    "trend": 1.0,
    "sentiment": 1.0
}

# =========================
# 📊 MOCK MARKET DATA
# =========================


def get_market_price():
    return random.randint(80, 150)


def get_news_sentiment():
    return random.choice(["POSITIVE", "NEGATIVE"])


# =========================
# 🤖 AI DECISION (Multi-factor)
# =========================
def generate_signal(price, sentiment):
    score = 0

    if price > 100:
        score += strategy_weights["trend"]

    if sentiment == "POSITIVE":
        score += strategy_weights["sentiment"]

    return "BUY" if score > 1 else "SELL"


# =========================
# ⚖️ RISK MANAGEMENT
# =========================
def calculate_position(balance):
    return balance * MAX_RISK


def stop_loss(entry, current):
    loss = (entry - current) / entry
    return loss > 0.02


# =========================
# 💰 TRADE EXECUTION (SIMULATED)
# =========================
def execute_trade(signal):
    print(f"Executing trade: {signal}")
    # simulate profit/loss
    return random.choice([10, -5, 15, -10])


# =========================
# 📊 PnL TRACKING
# =========================
trades = []


def log_trade(signal, profit):
    trades.append({"signal": signal, "profit": profit})


def total_pnl():
    return sum(t["profit"] for t in trades)


# =========================
# 🧠 LEARNING ENGINE
# =========================
def update_strategy(profit):
    if profit > 0:
        strategy_weights["trend"] += 0.1
        strategy_weights["sentiment"] += 0.1
    else:
        strategy_weights["trend"] -= 0.1
        strategy_weights["sentiment"] -= 0.1

    # clamp
    strategy_weights["trend"] = max(0.1, strategy_weights["trend"])
    strategy_weights["sentiment"] = max(0.1, strategy_weights["sentiment"])


# =========================
# 🔔 ALERT SYSTEM
# =========================
def notify(msg):
    print(f"🔔 ALERT: {msg}")


# =========================
# 🧠 MAIN LOOP (AUTO LEARNING)
# =========================
def run_bot():
    balance = 1000

    while True:
        print("\n🚀 Running AI Cycle...")

        price = get_market_price()
        sentiment = get_news_sentiment()

        print("Price:", price, "| Sentiment:", sentiment)

        signal = generate_signal(price, sentiment)
        print("Signal:", signal)

        position = calculate_position(balance)
        print("Position Size:", position)

        profit = execute_trade(signal)
        print("Trade Result:", profit)

        log_trade(signal, profit)
        update_strategy(profit)

        print("Total PnL:", total_pnl())
        print("Weights:", strategy_weights)

        notify(f"{signal} → Profit: {profit}")

        time.sleep(5)  # change to 300 for real


# =========================
# ▶️ START
# =========================
if __name__ == "__main__":
    run_bot()
