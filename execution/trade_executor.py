from agents.trading.binance_client import place_order
from risk.risk_manager import apply_risk_management
from portfolio.portfolio_manager import get_balance


def execute_trade(decision):
    balance = get_balance()
    risk_amount = apply_risk_management(balance)

    quantity = risk_amount / 10000  # simple calc

    if decision == "BUY":
        return place_order(side="BUY", quantity=quantity)
    elif decision == "SELL":
        return place_order(side="SELL", quantity=quantity)
    else:
        return "No trade"
