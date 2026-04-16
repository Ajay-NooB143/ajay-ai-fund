import random


class RLAgent:
    def predict(self, obs):
        return random.choice(["BUY", "SELL", "HOLD"])
