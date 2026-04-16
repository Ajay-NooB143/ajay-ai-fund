portfolio = {
    "balance": 1000,
    "positions": []
}

def update_balance(amount):
    portfolio["balance"] += amount

def get_balance():
    return portfolio["balance"]
