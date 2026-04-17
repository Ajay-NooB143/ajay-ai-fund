import streamlit as st

from analytics.performance import equity_curve, load_trades, performance_metrics

df = load_trades()

if df.empty:
    st.warning("No trade data available.")
else:
    stats = performance_metrics(df)

    st.title("💀 AI FUND PERFORMANCE")

    st.metric("Total Trades", stats["trades"])
    st.metric("Winrate", f"{stats['winrate'] * 100:.2f}%")
    st.metric("Profit", f"${stats['profit']:.2f}")
    st.metric("RR", f"{stats['rr']:.2f}")

    eq = equity_curve(df)
    st.line_chart(eq["equity"])
