"""A sequenced log and a deterministic matcher: a standby replaying it has the same book."""
import hashlib


class Engine:
    def __init__(self, clock=None):
        self.bids, self.asks = [], []        # (priority key, seq, id, qty), best first
        self.events = []
        self.clock = clock

    def apply(self, seq, stamp, oid, side, price, qty):
        """One log entry: all inputs come from the log, even the time."""
        now = self.clock() if self.clock else stamp
        rest, other = (self.bids, self.asks) if side == "buy" else (self.asks, self.bids)
        sign = 1 if side == "buy" else -1
        while qty and other and sign * (price - abs(other[0][0])) >= 0:
            key, s, mid, resting = other[0]
            traded = min(qty, resting)
            self.events.append(("trade", seq, now, oid, mid, abs(key), traded))
            qty -= traded
            if traded == resting:
                other.pop(0)
            else:
                other[0] = (key, s, mid, resting - traded)
        if qty:
            rest.append((-price if side == "buy" else price, seq, oid, qty))
            rest.sort()
            self.events.append(("rest", seq, now, oid, price, qty))

    def digest(self):
        text = repr((self.bids, self.asks, self.events))
        return hashlib.sha256(text.encode()).hexdigest()[:12]
