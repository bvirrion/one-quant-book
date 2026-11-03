class RunningStats:
    def __init__(self):
        self.n, self.mean, self.m2 = 0, 0.0, 0.0

    def add(self, x):
        self.n += 1
        d = x - self.mean
        self.mean += d / self.n
        self.m2 += d * (x - self.mean)

    def variance(self):               # the sample variance, for n >= 2
        return self.m2 / (self.n - 1)


# Not printed: the naive version and the remove step of the follow-up.
def naive_variance(xs):
    n = len(xs)
    s = sum(xs)
    q = sum(x * x for x in xs)
    return (q - s * s / n) / (n - 1)
