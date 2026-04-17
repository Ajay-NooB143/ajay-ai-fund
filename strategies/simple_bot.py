import os
import time

from binance.client import Client
import yfinance as yf

# =========================
# CONFIG
# =========================
LIVE_TRADING = False  # Turn True only when ready
SYMBOL = "BTCUSDT"
RISK_PERCENT = 0.01

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

client = Client(API_KEY, API_SECRET)


# =========================
# MARKET DATA
# =========================
def get_price():
    data = yf.download("BTC-USD", period="1d", interval="1m")
    return float(data["Close"].iloc[-1])


# =========================
# STRATEGY (simple but real)
# =========================
def generate_signal(price):
    if price > 50000:
        return "BUY"
    else:
        return "SELL"


# =========================
# RISK MANAGEMENT
# =========================
def get_balance():
    balance = client.get_asset_balance(asset="USDT")
    return float(balance["free"])


def calculate_quantity(balance, price):
    trade_amount = balance * RISK_PERCENT
    qty = trade_amount / price
    return round(qty, 5)


# =========================
# EXECUTION
# =========================
def place_order(signal, quantity):
    if not LIVE_TRADING:
        print(f"[SIMULATION] {signal} {quantity}")
        return {"status": "SIMULATED"}

    try:
        order = client.create_order(
            symbol=SYMBOL,
            side=signal,
            type="MARKET",
            quantity=quantity
        )
        return order
    except Exception as e:
        print("Order error:", e)
        return None


# =========================
# TRACKING
# =========================
pnl = 0


def update_pnl(result):
    global pnl
    if result:
        pnl += 1  # placeholder
    print("PnL:", pnl)


# =========================
# MAIN LOOP
# =========================
def run():
    while True:
        print("\nRunning cycle...")

        price = get_price()
        print("Price:", price)

        signal = generate_signal(price)
        print("Signal:", signal)

        balance = get_balance()
        print("Balance:", balance)

        qty = calculate_quantity(balance, price)
        print("Quantity:", qty)

        result = place_order(signal, qty)
        print("Result:", result)

        update_pnl(result)

        time.sleep(60)  # 1 minute


# =========================
# START
# =========================
if __name__ == "__main__":
    run()
