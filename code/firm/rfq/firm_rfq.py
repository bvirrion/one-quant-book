"""Request-for-quote auctions and composite prices (build of Book 2, Chapter 22).

A client sells a bond by request for quote to n dealers. Dealer i bids v - m + sigma * Z_i: the
common value v less a markup m, plus a private term (its inventory, its axes, its view). The client
sells to the best bid; each dealer that sees the request and loses may trade on what it learned,
costing the client `leak` on average. Prices and costs are in basis points of price.
"""
import math
import random
import statistics
from functools import cache


@cache
def expected_max_normal(n: int, steps: int = 8000) -> float:
    """E[max of n standard normals] = integral of x n phi(x) Phi(x)^(n-1), by the trapezoid rule."""
    if n == 1:
        return 0.0
    h, total = 16.0 / steps, 0.0
    for k in range(steps + 1):
        x = -8.0 + k * h
        f = x * n * math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi) * (0.5 * math.erfc(-x / math.sqrt(2))) ** (n - 1)
        total += f * (0.5 if k in (0, steps) else 1.0)
    return total * h


def expected_cost(n: int, markup: float, sigma: float, leak: float) -> float:
    """Client's expected cost of selling by RFQ to n dealers: markup less the best private term, plus
    leakage to the n - 1 losers."""
    return markup - sigma * expected_max_normal(n) + leak * (n - 1)


def best_n(markup: float, sigma: float, leak: float, n_max: int = 12) -> int:
    return min(range(1, n_max + 1), key=lambda n: expected_cost(n, markup, sigma, leak))


def simulate_rfq(n: int, markup: float, sigma: float, trials: int = 20_000, seed: int = 1) -> list[float]:
    """Winning-bid discount to value (bp) in simulated auctions."""
    rng = random.Random(seed)
    return [markup - max(sigma * rng.gauss(0, 1) for _ in range(n)) for _ in range(trials)]


def composite(quotes: list[tuple[float, float]], half_life: float = 60.0, k: float = 3.0) -> float:
    """Composite price from (price, age in seconds) quotes: drop outliers beyond k median absolute
    deviations of the median, then weight by recency with the given half-life."""
    prices = [p for p, _ in quotes]
    med = statistics.median(prices)
    mad = statistics.median(abs(p - med) for p in prices) or 1e-12
    kept = [(p, a) for p, a in quotes if abs(p - med) <= k * mad]
    w = [math.exp(-math.log(2) * a / half_life) for _, a in kept]
    return sum(wi * p for wi, (p, _) in zip(w, kept, strict=True)) / sum(w)
