"""Stress testing (build of One Quant Book 6, chapter 22).

A scenario is a vector of risk-factor moves. Historical scenarios are the moves between two dates of a
level history (differences for rates, log returns for prices). Hypothetical scenarios shock some factors
and fill the others by their conditional expectation under a covariance (Gaussian conditioning,
mu_u = S_us S_ss^-1 x_s). Reverse stress tests find the most plausible move - the smallest Mahalanobis
distance sqrt(x' S^-1 x) - that produces a given loss: in closed form for a linear book, by iterating
on the gradient direction for a non-linear one.
"""
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Scenario:
    name: str
    moves: np.ndarray        # one move per risk factor, in the model's units


def historical(name: str, dates: Sequence[str], levels: np.ndarray, start: str, end: str,
               log_cols: Sequence[int]) -> Scenario:
    """Moves between the levels on two dates: differences, or log returns for the columns in log_cols."""
    i, j = list(dates).index(start), list(dates).index(end)
    a, b = levels[i], levels[j]
    moves = np.array([math.log(b[k] / a[k]) if k in log_cols else b[k] - a[k] for k in range(len(a))])
    return Scenario(name, moves)


def condition(cov: np.ndarray, shocked: Sequence[int], values: Sequence[float]) -> np.ndarray:
    """Full move vector: the given shocks, the other factors at their conditional expectation."""
    n = cov.shape[0]
    s = list(shocked)
    u = [k for k in range(n) if k not in s]
    x = np.zeros(n)
    x[s] = values
    x[u] = cov[np.ix_(u, s)] @ np.linalg.solve(cov[np.ix_(s, s)], np.asarray(values, dtype=float))
    return x


def mahalanobis(x: np.ndarray, cov: np.ndarray) -> float:
    return float(math.sqrt(x @ np.linalg.solve(cov, x)))


def reverse_linear(delta: np.ndarray, cov: np.ndarray, loss: float) -> tuple[np.ndarray, float]:
    """Most plausible move with delta . x = -loss: x = -loss S delta / (delta' S delta)."""
    sd = cov @ delta
    x = -loss * sd / (delta @ sd)
    return x, loss / math.sqrt(delta @ sd)


def reverse_nonlinear(pnl: Callable[[np.ndarray], float], cov: np.ndarray, loss: float, x0: np.ndarray,
                      iters: int = 50, h: float = 1e-6) -> tuple[np.ndarray, float]:
    """Iterate: direction d = -S grad(pnl)(x), normalised to one Mahalanobis unit; move along it until
    pnl = -loss (bisection on the distance), recompute the gradient there."""
    x = np.asarray(x0, dtype=float)
    n = len(x)
    for _ in range(iters):
        g = np.array([(pnl(x + h * e) - pnl(x - h * e)) / (2 * h) for e in np.eye(n)])
        d = -(cov @ g)
        d = d / mahalanobis(d, cov)
        lo, hi = 0.0, 1.0
        while pnl(hi * d) > -loss:
            hi *= 2.0
            if hi > 64:
                raise ValueError("loss not reachable within 64 standard deviations")
        for _ in range(100):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if pnl(mid * d) > -loss else (lo, mid)
        new = 0.5 * (lo + hi) * d
        done = np.max(np.abs(new - x)) < 1e-12 * (1 + np.max(np.abs(x)))
        x = new
        if done:
            break
    return x, mahalanobis(x, cov)


def run(pnl: Callable[[np.ndarray], float], scenarios: Sequence[Scenario]) -> list[tuple[str, float]]:
    return [(s.name, float(pnl(s.moves))) for s in scenarios]
