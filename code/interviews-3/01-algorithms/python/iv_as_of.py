from bisect import bisect_right
from collections import defaultdict


class AsOfStore:
    def __init__(self):
        self.times = defaultdict(list)
        self.values = defaultdict(list)

    def set(self, key, value, t):     # times increase for each key
        self.times[key].append(t)
        self.values[key].append(value)

    def get(self, key, t):
        i = bisect_right(self.times.get(key, ()), t)  # a read adds no key
        return self.values[key][i - 1] if i else None


# Not printed: the follow-up.
def as_of_join(trades, quotes):
    """Both are sorted lists of (time, value). For each trade, the last quote at or before it."""
    out, i, last = [], 0, None
    for t, v in trades:
        while i < len(quotes) and quotes[i][0] <= t:
            last = quotes[i][1]
            i += 1
        out.append((t, v, last))
    return out
