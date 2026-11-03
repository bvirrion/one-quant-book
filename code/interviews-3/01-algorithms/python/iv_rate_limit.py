from collections import deque


class Limiter:
    """At most n accepted messages in any half-open time span of width t."""

    def __init__(self, n, t):
        self.n, self.t = n, t
        self.accepted = deque()

    def allow(self, now):             # times never go down
        while self.accepted and self.accepted[0] <= now - self.t:
            self.accepted.popleft()
        if len(self.accepted) == self.n:
            return False
        self.accepted.append(now)
        return True


# Not printed: the two cheaper limiters the answer compares.
class FixedBuckets:
    def __init__(self, n, t):
        self.n, self.t, self.bucket, self.used = n, t, None, 0

    def allow(self, now):
        b = now // self.t
        if b != self.bucket:
            self.bucket, self.used = b, 0
        if self.used == self.n:
            return False
        self.used += 1
        return True


class TokenBucket:
    def __init__(self, n, t):
        self.cap, self.rate, self.tokens, self.last = n, n / t, n, None

    def allow(self, now):
        if self.last is not None:
            self.tokens = min(self.cap, self.tokens + (now - self.last) * self.rate)
        self.last = now
        if self.tokens < 1:
            return False
        self.tokens -= 1
        return True
