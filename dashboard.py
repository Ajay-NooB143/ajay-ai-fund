import streamlit as st
from agents.forecaster.data_fetcher import get_stock_data
from agents.sentiment.sentiment_agent import analyze_sentiment
from agents.strategy import trading_decision
from execution.trade_executor import execute_trade

st.title("🤖 AI Trading Dashboard")

# Input
symbol = st.text_input("Enter Stock Symbol", "AAPL")
news = st.text_area("Enter News", "Apple stock is doing good")

if st.button("Run AI Trading"):
    data = get_stock_data(symbol)
    st.write("📊 Market Data:", data)

    sentiment = analyze_sentiment(news)
    st.write("🧠 Sentiment:", sentiment)

    decision = trading_decision(sentiment)
    st.write("📈 Decision:", decision)

    result = execute_trade(decision)
    st.write("💰 Trade Result:", result)
