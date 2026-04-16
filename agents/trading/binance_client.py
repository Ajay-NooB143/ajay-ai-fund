from binance.client import Client

API_KEY = Tlw8rEnaXMoW505RZmC6lWdSLsiN

SihHwgbaLnJjA61laBD8tTzNrBf4SM

MIrRUJ
API_SECRET = aDmNYQvUiFSN3mKZBV0UImpNIW 5r4Yyv314F71QR8fJ7902VN3qDeOS LKxPkfU4K

client = Client(API_KEY, API_SECRET)

def get_balance():
    return client.get_account()

def place_order(symbol="BTCUSDT", side="BUY", quantity=0.001):
    order = client.create_order(
        symbol=symbol,
        side=side,
        type="MARKET",
        quantity=quantity
    )
    return order
