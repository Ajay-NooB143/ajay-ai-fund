from agents.forecaster.data_fetcher import get_stock_data
from agents.sentiment.sentiment_agent import analyze_sentiment
from agents.strategy import trading_decision

def main():
    # Fetch market data
    data = get_stock_data("AAPL")
    print("Market Data:", data)

    # Fake news input
    news = "Apple stock is doing good"

    # Sentiment analysis
    sentiment = analyze_sentiment(news)
    print("Sentiment:", sentiment)

    # Trading decision
    decision = trading_decision(sentiment)
    print("Decision:", decision)

if __name__ == "__main__":
    main()
from agents.trading.binance_client import place_order

# After decision
if decision == "BUY":
    order = place_order(side="BUY")
    print("Order placed:", order)
