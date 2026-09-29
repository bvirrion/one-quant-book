"""Brute-force oracles for chapter 21's answers: slow, obviously correct."""
import itertools
import statistics


def pair_sum(sizes, target):
    for j in range(len(sizes)):
        for i in range(j):
            if sizes[i] + sizes[j] == target:
                return True
    return False


def sliding_max(prices, k):
    return [max(prices[i : i + k]) for i in range(len(prices) - k + 1)]


def rolling_median(xs, k):
    return [statistics.median(xs[max(0, i - k + 1) : i + 1]) for i in range(len(xs))]


def max_open(orders):
    pts = sorted({t for o in orders for t in o})
    return max((sum(s <= t < e for s, e in orders) for t in pts), default=0)


def best_k_trades(prices, k, fee=0.0):
    n, best = len(prices), 0.0
    for m in range(1, k + 1):
        for idx in itertools.combinations(range(n), 2 * m):
            profit = sum(prices[idx[2 * i + 1]] - prices[idx[2 * i]] - fee for i in range(m))
            best = max(best, profit)
    return best


def window_stats(xs, k):
    out = []
    for i in range(len(xs)):
        w = xs[max(0, i - k + 1) : i + 1]
        out.append((statistics.fmean(w), statistics.variance(w) if len(w) > 1 else 0.0))
    return out
