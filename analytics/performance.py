import os

import pandas as pd
import psycopg2


def load_trades():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    try:
        df = pd.read_sql("SELECT * FROM trades", conn)
    finally:
        conn.close()
    return df


def performance_metrics(df):
    total_trades = len(df)

    wins = df[df["pnl"] > 0]
    losses = df[df["pnl"] <= 0]

    winrate = len(wins) / total_trades if total_trades > 0 else 0

    total_profit = df["pnl"].sum()

    avg_win = wins["pnl"].mean() if len(wins) > 0 else 0
    avg_loss = losses["pnl"].mean() if len(losses) > 0 else 0

    rr = abs(avg_win / avg_loss) if avg_loss != 0 else 0

    return {
        "trades": total_trades,
        "winrate": winrate,
        "profit": total_profit,
        "rr": rr,
    }


def equity_curve(df):
    df = df.sort_values("time")
    df["equity"] = df["pnl"].cumsum()
    return df
