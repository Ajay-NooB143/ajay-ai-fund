import yfinance as yf


def get_stock_data(symbol="AAPL"):
    data = yf.download(symbol, period="1d", interval="1m")
    return data.tail()
