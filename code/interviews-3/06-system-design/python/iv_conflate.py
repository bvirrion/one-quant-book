"""Latest value per symbol: one entry each, served in the order they first went stale."""


class Conflator:
    def __init__(self):
        self.latest = {}

    def put(self, symbol, value):
        self.latest[symbol] = value          # a dict key keeps its first place when updated

    def take(self, n):
        out = []
        for symbol in list(self.latest)[:n]:
            out.append((symbol, self.latest.pop(symbol)))
        return out
