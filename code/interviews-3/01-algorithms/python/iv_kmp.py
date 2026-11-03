class Watcher:
    """Reports each position in a stream where the last m items equal the pattern."""

    def __init__(self, pattern):
        self.p = pattern
        self.fail = [0] * len(pattern)    # longest proper prefix that is also a suffix
        k = 0
        for i in range(1, len(pattern)):
            while k and pattern[i] != pattern[k]:
                k = self.fail[k - 1]
            k += pattern[i] == pattern[k]
            self.fail[i] = k
        self.k = 0                        # how much of the pattern the stream now ends with

    def push(self, x):
        while self.k and x != self.p[self.k]:
            self.k = self.fail[self.k - 1]
        self.k += x == self.p[self.k]
        if self.k == len(self.p):
            self.k = self.fail[-1]
            return True
        return False
