import argparse
import sys
import os

# Allow running from the repo root: python app/bot.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.forecaster.data_fetcher import get_stock_data
from agents.sentiment.sentiment_agent import analyze_sentiment
from agents.strategy import trading_decision
from execution.trade_executor import execute_trade


def run_bot(symbol: str, news: str) -> None:
    print(f"📡 Fetching market data for {symbol}...")
    data = get_stock_data(symbol)
    print("📊 Market Data:\n", data)

    print("\n🧠 Analysing sentiment...")
    sentiment = analyze_sentiment(news)
    print("Sentiment:", sentiment)

    print("\n📈 Making trading decision...")
    decision = trading_decision(sentiment)
    print("Decision:", decision)

    print("\n💰 Executing trade...")
    result = execute_trade(decision)
    print("Trade Result:", result)


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Trading Bot")
    parser.add_argument(
        "--symbol",
        default="AAPL",
        help="Stock/asset symbol to trade (default: AAPL)",
    )
    parser.add_argument(
        "--news",
        default="The market is performing steadily today.",
        help="News headline used for sentiment analysis",
    )
    args = parser.parse_args()

    run_bot(symbol=args.symbol, news=args.news)


if __name__ == "__main__":
    main()
