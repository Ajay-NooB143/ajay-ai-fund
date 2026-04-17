import os

import pandas as pd
import psycopg2
import streamlit as st

st.title("💀 AI FUND DASHBOARD")
st.write("System Running...")

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    try:
        conn = psycopg2.connect(DATABASE_URL)
        df = pd.read_sql("SELECT * FROM trades ORDER BY time DESC", conn)
        conn.close()

        if not df.empty:
            st.subheader("📈 Price Chart")
            st.line_chart(df["price"])

            st.subheader("📋 Recent Trades")
            st.write(df.tail())
        else:
            st.info("No trades recorded yet.")
    except Exception as exc:
        st.warning(f"Could not load trades: {exc}")
else:
    st.info("Set DATABASE_URL to enable trade history.")
