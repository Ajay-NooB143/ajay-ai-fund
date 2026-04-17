WARMUP_PERIOD = 50
INITIAL_BALANCE = 10000


def backtest(df, strategy_func, initial_balance=INITIAL_BALANCE, warmup_period=WARMUP_PERIOD):
    balance = initial_balance
    trades = []

    for i in range(warmup_period, len(df) - 1):
        data = df.iloc[:i]

        signal = strategy_func(data)

        price = df.iloc[i]["close"]
        next_price = df.iloc[i + 1]["close"]

        if signal == "BUY":
            pnl = next_price - price
        elif signal == "SELL":
            pnl = price - next_price
        else:
            pnl = 0

        balance += pnl
        trades.append(balance)

    return trades
