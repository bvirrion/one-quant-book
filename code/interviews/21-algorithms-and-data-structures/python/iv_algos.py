"""Book 18, chapter 21: answers to the algorithm questions, each with a brute-force oracle."""
import heapq
from bisect import bisect_left
from collections import deque
from math import log


def pair_sum(sizes, target):
    """Indices (i, j), i < j, of two sizes summing to target, or None. O(n) with a hash map."""
    seen = {}
    for j, x in enumerate(sizes):
        if target - x in seen:
            return seen[target - x], j
        seen.setdefault(x, j)
    return None


def first_duplicate(ids):
    seen = set()
    for x in ids:
        if x in seen:
            return x
        seen.add(x)
    return None


def merge_tapes(a, b):
    """Merge two lists of (time, payload) sorted by time; ties keep a before b. O(n + m)."""
    i = j = 0
    out = []
    while i < len(a) and j < len(b):
        if b[j][0] < a[i][0]:
            out.append(b[j])
            j += 1
        else:
            out.append(a[i])
            i += 1
    return out + a[i:] + b[j:]


def best_trade(prices):
    """Largest profit from one buy followed by one sell (0 if none is profitable). O(n)."""
    best, low = 0, float("inf")
    for p in prices:
        low = min(low, p)
        best = max(best, p - low)
    return best


def first_at_or_after(times, t):
    """Index of the first element >= t in a sorted list, or len(times)."""
    return bisect_left(times, t)


def sliding_max(prices, k):
    """Maximum of each window of k consecutive prices, with a monotonic deque of indices. O(n)."""
    dq, out = deque(), []
    for i, p in enumerate(prices):
        while dq and prices[dq[-1]] <= p:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - k:
            dq.popleft()
        if i >= k - 1:
            out.append(prices[dq[0]])
    return out


class RollingMedian:
    """Median of the last k values: two heaps with lazy deletion. O(log k) per update."""

    def __init__(self, k):
        self.k, self.lo, self.hi, self.gone, self.buf = k, [], [], {}, deque()
        self.nlo = self.nhi = 0

    def _prune(self, heap, sign):
        while heap and self.gone.get(sign * heap[0], 0):
            self.gone[sign * heap[0]] -= 1
            heapq.heappop(heap)

    def _balance(self):
        if self.nlo > self.nhi + 1:
            heapq.heappush(self.hi, -heapq.heappop(self.lo))
            self.nlo, self.nhi = self.nlo - 1, self.nhi + 1
            self._prune(self.lo, -1)
        elif self.nlo < self.nhi:
            heapq.heappush(self.lo, -heapq.heappop(self.hi))
            self.nlo, self.nhi = self.nlo + 1, self.nhi - 1
            self._prune(self.hi, 1)

    def push(self, x):
        if not self.lo or x <= -self.lo[0]:
            heapq.heappush(self.lo, -x)
            self.nlo += 1
        else:
            heapq.heappush(self.hi, x)
            self.nhi += 1
        self.buf.append(x)
        if len(self.buf) > self.k:
            old = self.buf.popleft()
            self.gone[old] = self.gone.get(old, 0) + 1
            if old <= -self.lo[0]:
                self.nlo -= 1
                if old == -self.lo[0]:
                    self._prune(self.lo, -1)
            else:
                self.nhi -= 1
                if old == self.hi[0]:
                    self._prune(self.hi, 1)
        self._balance()
        self._prune(self.lo, -1)
        self._prune(self.hi, 1)
        if self.nlo > self.nhi:
            return -self.lo[0]
        return (-self.lo[0] + self.hi[0]) / 2


def top_k(stream, k):
    """k symbols with the largest total volume from (symbol, volume) pairs: count, then a heap of size k."""
    tot = {}
    for s, v in stream:
        tot[s] = tot.get(s, 0) + v
    return [s for _, s in heapq.nlargest(k, ((v, s) for s, v in tot.items()))]


def max_open(orders):
    """Most orders open at once; an order (start, end) is open on [start, end)."""
    events = sorted([(s, 1) for s, _ in orders] + [(e, -1) for _, e in orders])
    best = cur = 0
    for _, d in events:  # at equal times the end (-1) sorts first
        cur += d
        best = max(best, cur)
    return best


def merge_halts(halts):
    """Merge overlapping or touching [start, end] intervals."""
    out = []
    for s, e in sorted(halts):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return [tuple(x) for x in out]


def arbitrage_cycle(rates):
    """True if some cycle of conversions multiplies money: a negative cycle in -log(rate) (Bellman-Ford)."""
    n = len(rates)
    w = [[-log(rates[i][j]) if rates[i][j] > 0 else None for j in range(n)] for i in range(n)]
    dist = [0.0] * n
    for _ in range(n - 1):
        for i in range(n):
            for j in range(n):
                if w[i][j] is not None and dist[i] + w[i][j] < dist[j] - 1e-12:
                    dist[j] = dist[i] + w[i][j]
    return any(w[i][j] is not None and dist[i] + w[i][j] < dist[j] - 1e-12 for i in range(n) for j in range(n))


def best_k_trades(prices, k, fee=0.0):
    """Largest profit with at most k non-overlapping buy-sell pairs, paying `fee` per round trip. O(nk)."""
    if not prices or k == 0:
        return 0.0
    hold = [float("-inf")] * (k + 1)
    free = [0.0] * (k + 1)
    for p in prices:
        for j in range(1, k + 1):
            hold[j] = max(hold[j], free[j - 1] - p)
            free[j] = max(free[j], hold[j] + p - fee)
    return max(free)


class PriceLevels:
    """One side of a book aggregated by price: add, cancel and best in O(log n) with a heap and lazy removal."""

    def __init__(self, bid=True):
        self.sign, self.qty, self.heap = (-1 if bid else 1), {}, []

    def add(self, price, q):
        if price not in self.qty or self.qty[price] == 0:
            heapq.heappush(self.heap, self.sign * price)
        self.qty[price] = self.qty.get(price, 0) + q

    def cancel(self, price, q):
        self.qty[price] -= q

    def best(self):
        while self.heap and self.qty.get(self.sign * self.heap[0], 0) == 0:
            heapq.heappop(self.heap)
        return self.sign * self.heap[0] if self.heap else None


class WindowStats:
    """Mean and variance of the last k values, updated in O(1) with Welford-style add and remove."""

    def __init__(self, k):
        self.k, self.buf, self.n, self.mean, self.m2 = k, deque(), 0, 0.0, 0.0

    def push(self, x):
        self.buf.append(x)
        self.n += 1
        d = x - self.mean
        self.mean += d / self.n
        self.m2 += d * (x - self.mean)
        if self.n > self.k:
            y = self.buf.popleft()
            self.n -= 1
            d = y - self.mean
            self.mean -= d / self.n
            self.m2 -= d * (y - self.mean)
        return self.mean, (self.m2 / (self.n - 1) if self.n > 1 else 0.0)
