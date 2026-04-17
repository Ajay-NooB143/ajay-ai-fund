import os

import pandas as pd
import psycopg2
import streamlit as st

st.title("💀 AI FUND DASHBOARD")
st.write("System Running...")

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            df = pd.read_sql(
                "SELECT * FROM trades ORDER BY time DESC", conn,
            )

        if not df.empty:
            st.subheader("📈 Price Chart")
            st.line_chart(df.set_index("time")["price"])

            st.subheader("📋 Recent Trades")
            st.write(df.head())
        else:
            st.info("No trades recorded yet.")
    except Exception as exc:
        st.warning(f"Could not load trades: {exc}")
else:
    st.info("Set DATABASE_URL to enable trade history.")
