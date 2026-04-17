strategy_weights = {
    "trend": 1.0,
    "sentiment": 1.0
}


def generate_signal(price, sentiment):
    score = 0

    if price > 100:
        score += strategy_weights["trend"]

    if sentiment == "POSITIVE":
        score += strategy_weights["sentiment"]

    return "BUY" if score > 1 else "SELL"


def my_function():
    pass
