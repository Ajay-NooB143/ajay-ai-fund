def trading_decision(sentiment):
    if sentiment == "POSITIVE":
        return "BUY"
    elif sentiment == "NEGATIVE":
        return "SELL"
    else:
        return "HOLD"
