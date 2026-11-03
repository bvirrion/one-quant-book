import math


class Ewma:
    """Same numbers as pandas ewm(alpha=alpha, adjust=True, ignore_na=False)."""

    def __init__(self, alpha):
        self.keep = 1.0 - alpha
        self.num = self.den = 0.0
        self.mean = math.nan

    def update(self, x):
        self.num *= self.keep
        self.den *= self.keep
        if not math.isnan(x):
            self.num += x
            self.den += 1.0
            self.mean = self.num / self.den
        return self.mean


class TimeEwma:
    """Weights fall by half every halflife, whatever the spacing of the ticks."""

    def __init__(self, halflife):
        self.rate = math.log(2.0) / halflife
        self.num = self.den = 0.0
        self.t, self.mean = None, math.nan

    def update(self, t, x):
        if self.t is not None:
            keep = math.exp(-self.rate * (t - self.t))
            self.num *= keep
            self.den *= keep
        self.t = t
        if not math.isnan(x):                 # a NaN ages the weights, adds nothing
            self.num += x
            self.den += 1.0
            self.mean = self.num / self.den
        return self.mean
