def trading_decision(sentiment):
    if sentiment == "positive":
        return "BUY"
    elif sentiment == "negative":
        return "SELL"
    else:
        return "HOLD"
