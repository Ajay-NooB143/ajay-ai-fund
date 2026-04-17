import streamlit as st
from agents.forecaster.data_fetcher import get_stock_data
from agents.sentiment.sentiment_agent import analyze_sentiment
from agents.strategy import trading_decision
from execution.trade_executor import execute_trade
from risk.risk_calculator import full_trade_plan
from risk.leverage_optimizer import optimize_leverage
from analytics.support_resistance import detect_support_resistance

st.title("🤖 AI Trading Dashboard")

# ── Tab layout ────────────────────────────────────────────────────────────────
tab_trade, tab_risk, tab_leverage, tab_sr = st.tabs([
    "📈 AI Trading",
    "🛡️ Risk Calculator",
    "⚡ Leverage Optimizer",
    "📐 Support / Resistance",
])

# ── Tab 1: AI Trading ─────────────────────────────────────────────────────────
with tab_trade:
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

# ── Tab 2: Risk Calculator ────────────────────────────────────────────────────
with tab_risk:
    st.header("🛡️ Risk Calculator")
    st.caption("Calculates position size, stop-loss, take-profit and R:R ratio.")

    col1, col2 = st.columns(2)
    with col1:
        rc_balance = st.number_input("Account Balance ($)", value=10000.0, min_value=1.0, key="rc_balance")
        rc_risk_pct = st.number_input("Risk per Trade (%)", value=1.0, min_value=0.1, max_value=100.0, key="rc_risk")
        rc_side = st.selectbox("Trade Side", ["BUY", "SELL"], key="rc_side")
    with col2:
        rc_entry = st.number_input("Entry Price", value=100.0, min_value=0.0001, key="rc_entry")
        rc_sl = st.number_input("Stop-Loss Price", value=98.0, min_value=0.0001, key="rc_sl")
        rc_rr = st.number_input("Reward : Risk Ratio", value=2.0, min_value=0.1, key="rc_rr")

    if st.button("Calculate Trade Plan", key="rc_btn"):
        plan = full_trade_plan(
            balance=rc_balance,
            risk_percent=rc_risk_pct,
            entry_price=rc_entry,
            stop_loss_price=rc_sl,
            reward_ratio=rc_rr,
            side=rc_side,
        )
        if "error" in plan:
            st.error(plan["error"])
        else:
            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("Position Size", f"{plan['position_size']:.4f}")
            col_b.metric("Risk Amount ($)", f"${plan['risk_amount']:.2f}")
            col_c.metric("Take-Profit", f"{plan['take_profit_price']:.4f}")
            col_d.metric("R:R Ratio", f"{plan['risk_reward_ratio']:.2f}")
            st.caption(f"Stop distance: {plan['stop_distance_pct']:.2f}% from entry")

# ── Tab 3: Leverage Optimizer ─────────────────────────────────────────────────
with tab_leverage:
    st.header("⚡ Leverage Optimizer")
    st.caption(
        "Suggests the safest leverage that keeps your risk within limits. "
        "Provide recent OHLC data for a volatility-adjusted recommendation."
    )

    col1, col2 = st.columns(2)
    with col1:
        lv_balance = st.number_input("Account Balance ($)", value=10000.0, min_value=1.0, key="lv_balance")
        lv_risk_pct = st.number_input(
            "Max Risk per Trade (%)",
            value=1.0, min_value=0.1, max_value=100.0, key="lv_risk",
        )
        lv_max_lev = st.slider("Platform Max Leverage", min_value=1, max_value=125, value=20, key="lv_max")
    with col2:
        lv_entry = st.number_input("Entry Price", value=100.0, min_value=0.0001, key="lv_entry")
        lv_sl = st.number_input("Stop-Loss Price", value=98.0, min_value=0.0001, key="lv_sl")

    lv_use_ohlc = st.checkbox("Use OHLC data for volatility adjustment", value=False, key="lv_ohlc_toggle")
    lv_high_input = lv_low_input = lv_close_input = ""
    if lv_use_ohlc:
        st.caption("Paste comma-separated values (oldest → newest) for each series:")
        lv_high_input = st.text_area("High prices", key="lv_high_input")
        lv_low_input = st.text_area("Low prices", key="lv_low_input")
        lv_close_input = st.text_area("Close prices", key="lv_close_input")

    if st.button("Optimize Leverage", key="lv_btn"):
        high_prices, low_prices, close_prices = [], [], []
        if lv_use_ohlc:
            try:
                if lv_high_input.strip():
                    high_prices = [float(x) for x in lv_high_input.split(",") if x.strip()]
                if lv_low_input.strip():
                    low_prices = [float(x) for x in lv_low_input.split(",") if x.strip()]
                if lv_close_input.strip():
                    close_prices = [float(x) for x in lv_close_input.split(",") if x.strip()]
            except ValueError:
                st.error("Invalid price data – enter comma-separated numbers.")
                high_prices = low_prices = close_prices = []

        result = optimize_leverage(
            balance=lv_balance,
            entry_price=lv_entry,
            stop_loss_price=lv_sl,
            max_risk_percent=lv_risk_pct,
            max_leverage=lv_max_lev,
            high=high_prices if high_prices else None,
            low=low_prices if low_prices else None,
            close=close_prices if close_prices else None,
        )
        if "error" in result:
            st.error(result["error"])
        else:
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Suggested Leverage", f"{result['suggested_leverage']}x")
            col_b.metric("Position Size", f"{result['position_size']:.4f}")
            col_c.metric("Risk Amount ($)", f"${result['risk_amount']:.2f}")
            if result["atr"] > 0:
                st.caption(
                    f"ATR: {result['atr']:.4f} | "
                    f"Volatility adjustment factor: {result['volatility_factor']:.2f}"
                )

# ── Tab 4: Support / Resistance ───────────────────────────────────────────────
with tab_sr:
    st.header("📐 Auto Support / Resistance")
    st.caption(
        "Paste OHLC price series to automatically detect and update "
        "support and resistance zones using pivot-point analysis."
    )

    sr_symbol = st.text_input("Symbol (for live fetch)", "AAPL", key="sr_symbol")
    sr_use_live = st.checkbox("Fetch live data", value=True, key="sr_live")

    if not sr_use_live:
        st.caption("Paste comma-separated values (oldest → newest) for each series:")
        sr_high_input = st.text_area("High prices", key="sr_high")
        sr_low_input = st.text_area("Low prices", key="sr_low")
        sr_close_input = st.text_area("Close prices", key="sr_close")

    sr_window = st.slider("Pivot window", min_value=2, max_value=20, value=5, key="sr_window")
    sr_tol = st.slider("Cluster tolerance (%)", min_value=0.1, max_value=5.0, value=0.5, step=0.1, key="sr_tol")
    sr_max = st.slider("Max levels per side", min_value=1, max_value=10, value=5, key="sr_max")

    if st.button("Detect Levels", key="sr_btn"):
        high_list, low_list, close_list = [], [], []

        if sr_use_live:
            raw = get_stock_data(sr_symbol)
            if raw is not None and not raw.empty:
                high_list = raw["High"].tolist()
                low_list = raw["Low"].tolist()
                close_list = raw["Close"].tolist()
            else:
                st.error("Could not fetch live data.")
        else:
            try:
                high_list = [float(x) for x in sr_high_input.split(",") if x.strip()]
                low_list = [float(x) for x in sr_low_input.split(",") if x.strip()]
                close_list = [float(x) for x in sr_close_input.split(",") if x.strip()]
            except ValueError:
                st.error("Invalid price data – enter comma-separated numbers.")

        if high_list and low_list and close_list:
            levels = detect_support_resistance(
                high=high_list,
                low=low_list,
                close=close_list,
                window=sr_window,
                tolerance_pct=sr_tol,
                max_levels=sr_max,
            )
            if "error" in levels:
                st.error(levels["error"])
            else:
                st.metric("Current Price", f"{levels['current_price']:.4f}")

                col_r, col_s = st.columns(2)
                with col_r:
                    st.subheader("🔴 Resistance Levels")
                    if levels["resistance_levels"]:
                        for lvl in levels["resistance_levels"]:
                            pct = (lvl - levels["current_price"]) / levels["current_price"] * 100
                            st.write(f"**{lvl:.4f}** (+{pct:.2f}%)")
                    else:
                        st.info("No resistance levels detected above current price.")
                with col_s:
                    st.subheader("🟢 Support Levels")
                    if levels["support_levels"]:
                        for lvl in levels["support_levels"]:
                            pct = (levels["current_price"] - lvl) / levels["current_price"] * 100
                            st.write(f"**{lvl:.4f}** (-{pct:.2f}%)")
                    else:
                        st.info("No support levels detected below current price.")
