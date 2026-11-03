import time


class Throttled:
    """Sends at most one order per second, on every tick above a level."""

    def __init__(self, gateway, level):
        self.gateway, self.level = gateway, level
        self.last = 0.0

    def on_tick(self, price):
        now = time.time()
        if price > self.level and now - self.last >= 1.0:
            self.last = now
            self.gateway.send(price)
