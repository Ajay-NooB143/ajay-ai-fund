from agents.forecaster.data_fetcher import get_stock_data
from agents.sentiment.sentiment_agent import analyze_sentiment
from agents.strategy import trading_decision
from execution.trade_executor import execute_trade

def main():
    data = get_stock_data("AAPL")
    print("Market Data:", data)

    news = "Apple stock is performing very good"

    sentiment = analyze_sentiment(news)
    print("Sentiment:", sentiment)

    decision = trading_decision(sentiment)
    print("Decision:", decision)

    result = execute_trade(decision)
    print("Trade Result:", result)

if __name__ == "__main__":
    main()
