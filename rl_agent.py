class RLAgent:
    def decide(self, features):
        # state: price, orderbook, indicators
        # action: buy / sell / hold
        return "BUY"


def smart_execute(signal, orderbook):
    spread = float(orderbook['asks'][0][0]) - float(orderbook['bids'][0][0])
    if spread < 0.5:
        return "LIMIT ORDER"
    else:
        return "WAIT"