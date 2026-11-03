"""A cumulative price, the sum of price times seconds. Two readings give the average."""


class Accumulator:
    def __init__(self, t0, price):
        self.t, self.price, self.total = t0, price, 0

    def update(self, t, price):
        self.total += self.price * (t - self.t)
        self.t, self.price = t, price

    def read(self, t):
        return self.total + self.price * (t - self.t), t


def twap(first, second):
    return (second[0] - first[0]) / (second[1] - first[1])
