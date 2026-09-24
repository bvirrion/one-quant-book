"""firm.impulse -- hedging bands and stopping thresholds (One Quant Book 4, chapter 10).

An exposure X moves as a Brownian motion with variance sigma^2 per unit time (client flows); holding
it costs gamma X^2 per unit time (a risk charge); a hedge trade costs a fixed K plus c per unit
traded. A band policy trades back to +-a whenever |X| reaches b. Renewal-reward gives its long-run
average cost exactly; the optimum over (a, b) is found by golden-section search.

API (stable):
    band_cost(b, a, sigma, gamma, K, c)           long-run average cost of the (a, b) band policy
    reflect_cost(b, sigma, gamma, c)              average cost of reflecting at +-b (no fixed cost)
    optimal_fixed_band(sigma, gamma, K)           b* = (6 K sigma^2 / gamma)^(1/4), reset to zero
    optimal_proportional_band(sigma, gamma, c)    b* = (3 c sigma^2 / (4 gamma))^(1/3)
    optimal_band(sigma, gamma, K, c)              numerical optimum (a*, b*, cost)
    simulate_band(b, a, sigma, gamma, K, c, T, dt, seed) -> average cost and trade count
    stop_threshold_drift(mu, sigma, r, cost)      perpetual stopping of X = x + mu t + sigma W:
                                                  sell at b* = cost + 1/theta (smooth pasting)
    golden(f, lo, hi)                             minimiser on an interval
"""
from __future__ import annotations

import math

import numpy as np


def band_cost(b: float, a: float, sigma: float, gamma: float, K: float, c: float = 0.0) -> float:
    """Average cost per unit time: [K + c (b - a) + gamma (b^4 - a^4) / (6 sigma^2)] sigma^2 / (b^2 - a^2).

    A cycle starts at +-a and ends when |X| = b; E[cycle length] = (b^2 - a^2) / sigma^2 and
    E[int X^2 dt] = (b^4 - a^4) / (6 sigma^2) solve (1/2) sigma^2 f'' = -1 and -x^2 with f(+-b) = 0."""
    if not 0 <= a < b:
        return math.inf
    per_cycle = K + c * (b - a) + gamma * (b**4 - a**4) / (6 * sigma**2)
    return per_cycle * sigma**2 / (b**2 - a**2)


def reflect_cost(b: float, sigma: float, gamma: float, c: float) -> float:
    """Reflected Brownian motion on [-b, b]: uniform stationary law, E[X^2] = b^2 / 3, and the
    boundaries push at total rate sigma^2 / (2 b)."""
    return c * sigma**2 / (2 * b) + gamma * b**2 / 3


def optimal_fixed_band(sigma: float, gamma: float, K: float) -> tuple[float, float]:
    b = (6 * K * sigma**2 / gamma) ** 0.25
    return b, band_cost(b, 0.0, sigma, gamma, K)


def optimal_proportional_band(sigma: float, gamma: float, c: float) -> tuple[float, float]:
    b = (3 * c * sigma**2 / (4 * gamma)) ** (1 / 3)
    return b, reflect_cost(b, sigma, gamma, c)


def golden(f, lo: float, hi: float, n: int = 100) -> float:
    g = (math.sqrt(5) - 1) / 2
    for _ in range(n):
        x1, x2 = hi - g * (hi - lo), lo + g * (hi - lo)
        if f(x1) < f(x2):
            hi = x2
        else:
            lo = x1
    return 0.5 * (lo + hi)


def optimal_band(sigma: float, gamma: float, K: float, c: float) -> tuple[float, float, float]:
    """Minimise band_cost over the reset level a (inner search) and the trigger b (outer search)."""
    def best_a(b):
        a = golden(lambda a: band_cost(b, a, sigma, gamma, K, c), 0.0, 0.999 * b)
        return a, band_cost(b, a, sigma, gamma, K, c)

    scale = (6 * K * sigma**2 / gamma) ** 0.25 + (3 * c * sigma**2 / gamma) ** (1 / 3) + 1e-9
    b = golden(lambda b: best_a(b)[1], 1e-6 * scale, 5 * scale)
    a, cost = best_a(b)
    return a, b, cost


def simulate_band(b: float, a: float, sigma: float, gamma: float, K: float, c: float, T: float, dt: float,
                  seed: int) -> dict:
    """Simulate the exposure with the band policy on a grid; returns the average cost per unit time
    and the number of trades. Discrete monitoring overshoots the band slightly."""
    rng = np.random.default_rng(seed)
    n = int(T / dt)
    x, cost, trades = 0.0, 0.0, 0
    dw = sigma * math.sqrt(dt) * rng.standard_normal(n)
    for k in range(n):
        x += dw[k]
        cost += gamma * x * x * dt
        if abs(x) >= b:
            target = math.copysign(a, x)
            cost += K + c * abs(x - target)
            x = target
            trades += 1
    return {"avg_cost": cost / T, "trades": trades}


def stop_threshold_drift(mu: float, sigma: float, r: float, cost: float) -> tuple[float, float]:
    """Stop X_t = x + mu t + sigma W_t to collect X - cost, discounting at r. For x below the threshold
    V(x) = (b - cost) exp(theta (x - b)) with theta the positive root of sigma^2 th^2 / 2 + mu th - r = 0;
    smooth pasting V'(b) = 1 gives b* = cost + 1 / theta. Returns (b*, theta)."""
    theta = (-mu + math.sqrt(mu * mu + 2 * r * sigma * sigma)) / (sigma * sigma)
    return cost + 1 / theta, theta
