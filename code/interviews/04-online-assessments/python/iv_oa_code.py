"""Book 18, chapter 4: the two automated-coding-assessment answers and their brute-force oracles."""
from bisect import bisect_left, bisect_right


def longest_rising_run(prices):
    """Length of the longest run of strictly increasing consecutive prices. O(n) time, O(1) memory."""
    best = run = 0
    prev = None
    for p in prices:
        run = run + 1 if prev is not None and p > prev else 1
        best = max(best, run)
        prev = p
    return best


def longest_rising_run_oracle(prices):
    n, best = len(prices), 0
    for i in range(n):
        j = i
        while j + 1 < n and prices[j + 1] > prices[j]:
            j += 1
        best = max(best, j - i + 1)
    return best


class PriceWindowCounter:
    """Count trades with price in [lo, hi]: sort once, O(n log n); each query O(log n)."""

    def __init__(self, prices):
        self.s = sorted(prices)

    def count(self, lo, hi):
        if lo > hi:
            return 0
        return bisect_right(self.s, hi) - bisect_left(self.s, lo)


def count_oracle(prices, lo, hi):
    return sum(lo <= p <= hi for p in prices)
