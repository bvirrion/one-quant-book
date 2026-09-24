"""Hedging-programme evaluator (build of Book 3, Chapter 12).

Instruments are payoffs per barrel on a settlement price (the average over the hedged period for
average-price instruments). Prices of vanilla options on futures use Black's formula; average-price
options are valued by Monte Carlo on a lognormal futures price (numpy only, fixed seeds).
"""
import math
from dataclasses import dataclass

import numpy as np


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def black76(f: float, k: float, t: float, sigma: float, r: float, call: bool) -> float:
    """Black's price of a European option on a future (money paid at expiry, discounted at r)."""
    if t <= 0 or sigma <= 0:
        return math.exp(-r * t) * max((f - k) if call else (k - f), 0.0)
    d1 = (math.log(f / k) + 0.5 * sigma * sigma * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)
    if call:
        return math.exp(-r * t) * (f * norm_cdf(d1) - k * norm_cdf(d2))
    return math.exp(-r * t) * (k * norm_cdf(-d2) - f * norm_cdf(-d1))


@dataclass(frozen=True)
class Leg:
    """One instrument per barrel: kind in swap, put, call; side +1 bought, -1 sold."""
    kind: str
    strike: float
    side: int = 1

    def payoff(self, x: np.ndarray) -> np.ndarray:
        if self.kind == "swap":                         # a producer sells a swap: receives strike - x
            return self.side * (x - self.strike)
        if self.kind == "put":
            return self.side * np.maximum(self.strike - x, 0.0)
        if self.kind == "call":
            return self.side * np.maximum(x - self.strike, 0.0)
        raise ValueError(self.kind)


def collar(put_strike: float, call_strike: float) -> list[Leg]:
    """Producer's collar: buy a put, sell a call."""
    return [Leg("put", put_strike, 1), Leg("call", call_strike, -1)]


def three_way(put_strike: float, lower_put: float, call_strike: float) -> list[Leg]:
    """Producer's three-way collar: buy a put, sell a lower put, sell a call."""
    return [Leg("put", put_strike, 1), Leg("put", lower_put, -1), Leg("call", call_strike, -1)]


def simulate_averages(f0: float, sigma: float, t: float, steps: int, n: int, seed: int = 7) -> np.ndarray:
    """Arithmetic averages over `steps` equally spaced fixings in (0, t] of a driftless lognormal
    futures price (the risk-neutral dynamics of a future)."""
    rng = np.random.default_rng(seed)
    dt = t / steps
    z = rng.standard_normal((n, steps))
    logf = np.log(f0) + np.cumsum(-0.5 * sigma * sigma * dt + sigma * math.sqrt(dt) * z, axis=1)
    return np.exp(logf).mean(axis=1)


def value(legs: list[Leg], settlements: np.ndarray, r: float, t: float) -> float:
    """Discounted mean payoff per barrel of a set of legs on simulated settlement prices."""
    total = sum(leg.payoff(settlements) for leg in legs)
    return float(math.exp(-r * t) * np.mean(total))


def hedged_revenue(price: np.ndarray, legs: list[Leg], premium: float) -> np.ndarray:
    """Revenue per barrel of a producer selling at `price` with the legs' payoffs, net of the premium."""
    return price + sum(leg.payoff(price) for leg in legs) - premium


def cash_flow_at_risk(revenue: np.ndarray, budget: float, q: float = 0.05) -> float:
    """Shortfall of the q-quantile revenue below the budget (zero if the quantile meets it)."""
    return max(budget - float(np.quantile(revenue, q)), 0.0)
