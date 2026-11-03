class Throttled:
    """The same logic: the time and the way out are given to it."""

    def __init__(self, clock, gateway, level):
        self.clock, self.gateway, self.level = clock, gateway, level
        self.last = float("-inf")

    def on_tick(self, price):
        now = self.clock.now()
        if price > self.level and now - self.last >= 1.0:
            self.last = now
            self.gateway.send(price)


class SimClock:
    """In a backtest the replay loop moves this clock to each event's timestamp."""

    def __init__(self):
        self.t = 0.0

    def now(self):
        return self.t
