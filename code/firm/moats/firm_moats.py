"""firm.moats -- market concentration and free entry for trading businesses (build of One Quant Book 16,
chapter 30).

Shares (fractions summing to one) give the Herfindahl-Hirschman index on the 0-10,000 scale and concentration
ratios; partial public data (n firms, the top k's combined share) give bounds on the index. A symmetric Cournot
market with linear demand and a fixed cost per firm gives each firm's gross profit S / (n + 1)^2, where
S = (a - c)^2 / b, and the free-entry number of firms; an asymmetric-cost version gives shares, the price and the
effect of a merger with marginal-cost or fixed-cost synergies.

API (stable):
    hhi(shares) ; cr(shares, k) ; hhi_bounds(n, top_share, k=2)
    free_entry(S, F) ; welfare(S, F, n) ; planner(S, F)
    cournot(a, b, costs) -> dict ; merge(a, b, costs, i, j, synergy=0.0) -> dict ; synergy_for_price(a, costs, i, j)
    scenarios(S, fixed_costs) -> list of (F, n, hhi)
"""
import math

import numpy as np


def hhi(shares):
    """Sum of squared shares in percent (0 to 10,000)."""
    s = np.asarray(shares, float)
    return float(((100 * s / s.sum()) ** 2).sum())


def cr(shares, k):
    """Combined share of the k largest firms."""
    s = np.sort(np.asarray(shares, float) / np.sum(shares))[::-1]
    return float(s[:k].sum())


def hhi_bounds(n, top_share, k=2, grid=2001):
    """Smallest and largest index over n-firm share vectors whose k largest hold `top_share`.
    Minimum: the top k equal and the rest equal. Maximum: search over the k-th largest
    share b; one leader holds the rest of the top share, the other k - 1 hold b, and
    the remaining firms are packed at b with one remainder."""
    rest = 1 - top_share
    x = rest / (n - k)
    if x > top_share / k + 1e-12:
        raise ValueError("the others cannot all be smaller than the top firms")
    lo = hhi([top_share / k] * k + [x] * (n - k))
    best = lo
    for b in np.linspace(x, top_share / k, grid):
        full = min(n - k, int(rest / b + 1e-9))
        others = [b] * full + ([rest - full * b] if full < n - k else [])
        best = max(best, hhi([top_share - (k - 1) * b] + [b] * (k - 1) + others))
    return lo, best


def free_entry(S, F):
    """The largest n with S / (n + 1)^2 >= F: firms enter while the next covers its cost."""
    return max(0, math.floor(math.sqrt(S / F) + 1e-12) - 1)


def welfare(S, F, n):
    """Total surplus with n symmetric Cournot firms: consumers' surplus plus profits,
    less fixed costs."""
    return S * (n * n / 2 + n) / (n + 1) ** 2 - n * F


def planner(S, F, nmax=200):
    """The number of firms that maximises total surplus."""
    return max(range(1, nmax + 1), key=lambda n: welfare(S, F, n))


def cournot(a, b, costs):
    """Cournot equilibrium, inverse demand a - bQ, marginal costs `costs` (all active)."""
    c = np.asarray(costs, float)
    n = len(c)
    price = (a + c.sum()) / (n + 1)
    q = (price - c) / b
    if (q <= 0).any():
        raise ValueError("a firm would not produce; drop it and recompute")
    return {"price": price, "q": q, "profit": b * q * q, "shares": q / q.sum(), "hhi": hhi(q),
            "cs": b * q.sum() ** 2 / 2}


def merge(a, b, costs, i, j, synergy=0.0):
    """Firms i and j merge into one with marginal cost min(c_i, c_j) - synergy."""
    c = [x for k, x in enumerate(costs) if k not in (i, j)] + [min(costs[i], costs[j]) - synergy]
    return cournot(a, b, c)


def synergy_for_price(a, costs, i, j):
    """The marginal-cost synergy that leaves the Cournot price unchanged after i and j merge."""
    n = len(costs)
    before = (a + sum(costs)) / (n + 1)
    others = sum(x for k, x in enumerate(costs) if k not in (i, j))
    return a + others + min(costs[i], costs[j]) - n * before


def scenarios(S, fixed_costs):
    """(F, free-entry n, symmetric index) for each fixed cost."""
    out = []
    for F in fixed_costs:
        n = free_entry(S, F)
        out.append((F, n, 10_000 / n if n else float("nan")))
    return out
