def apply_risk_management(balance, risk_percent=1):
    risk_amount = balance * (risk_percent / 100)
    return risk_amount
