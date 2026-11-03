from collections import OrderedDict


class FirstUnique:
    def __init__(self):
        self.once = OrderedDict()     # seen exactly once, in order of arrival
        self.repeated = set()

    def add(self, symbol):
        if symbol in self.repeated:
            return
        if symbol in self.once:
            del self.once[symbol]
            self.repeated.add(symbol)
        else:
            self.once[symbol] = True

    def first_unique(self):
        return next(iter(self.once), None)
