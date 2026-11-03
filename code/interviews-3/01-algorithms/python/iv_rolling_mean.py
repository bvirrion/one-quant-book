class RollingMean:
    def __init__(self, k):
        self.k = k
        self.buf = [0] * k        # the last k values, overwritten in a circle
        self.n = 0                # how many values have arrived
        self.total = 0

    def update(self, x):
        i = self.n % self.k
        if self.n >= self.k:
            self.total -= self.buf[i]
        self.buf[i] = x
        self.total += x
        self.n += 1
        return self.total / min(self.n, self.k)
