"""firm.stochint -- discrete stochastic integrals for backtests (One Quant Book 4, chapter 3).

A backtest's P&L is a discrete stochastic integral: the position held over (t_i, t_{i+1}] times the
price change over that interval. The integral is an Ito integral, and the P&L honest, only if
the position is fixed at t_i with information available at t_i. A position that also uses the
price at t_{i+1} earns, on top, the covariation of the position with the price: a look-ahead
profit that exists on a pure random walk.

API (stable):
    gains(theta, s)                 -> cumulative P&L, position theta[i] earns s[i+1] - s[i]
    same_bar_gains(theta, s)        -> cumulative P&L with theta[i+1] credited with s[i+1] - s[i]
    covariation(x, y)               -> cumulative sum of (x[i+1] - x[i]) (y[i+1] - y[i])
    lookahead_test(theta, s)        -> dict: same-bar minus adapted P&L, the covariation it equals,
                                       and a t-statistic of the mean per-step gap
    riemann_sums(h, x, point)       -> sum of h(point in each interval) * increment of x
"""
from __future__ import annotations

import math

import numpy as np


def gains(theta: np.ndarray, s: np.ndarray) -> np.ndarray:
    """Adapted (Ito) gains: position theta[i], chosen at t_i, earns s[i+1] - s[i].

    theta and s have the same length n + 1; the result has length n + 1 and starts at zero."""
    th, x = np.asarray(theta, dtype=float), np.asarray(s, dtype=float)
    if th.shape != x.shape:
        raise ValueError("theta and s must be aligned on the same times")
    return np.concatenate([[0.0], np.cumsum(th[:-1] * np.diff(x))])


def same_bar_gains(theta: np.ndarray, s: np.ndarray) -> np.ndarray:
    """Anticipating gains: the position chosen at t_{i+1} is credited with the move into t_{i+1}."""
    th, x = np.asarray(theta, dtype=float), np.asarray(s, dtype=float)
    return np.concatenate([[0.0], np.cumsum(th[1:] * np.diff(x))])


def covariation(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Realised covariation [x, y] accumulated along the grid (quadratic variation when x is y)."""
    return np.concatenate([[0.0], np.cumsum(np.diff(np.asarray(x, float)) * np.diff(np.asarray(y, float)))])


def lookahead_test(theta: np.ndarray, s: np.ndarray) -> dict:
    """Same-bar minus adapted P&L is exactly the covariation of position and price; its per-step
    mean should be zero for an honest backtest, and is positive for a rule that reads the bar."""
    gap = same_bar_gains(theta, s) - gains(theta, s)
    cov = covariation(theta, s)
    steps = np.diff(np.asarray(theta, float)) * np.diff(np.asarray(s, float))
    t = steps.mean() / (steps.std(ddof=1) / math.sqrt(steps.size))
    return {"gap": float(gap[-1]), "covariation": float(cov[-1]), "t": float(t),
            "identity_error": float(np.max(np.abs(gap - cov)))}


def riemann_sums(h, x: np.ndarray, point: str = "left") -> float:
    """Sum of h(x at the chosen point) times the increment of x: 'left' (Ito), 'right', or
    'mid' (average of the two endpoint values of h: Stratonovich)."""
    x = np.asarray(x, dtype=float)
    dx = np.diff(x)
    hl, hr = h(x[:-1]), h(x[1:])
    val = {"left": hl, "right": hr, "mid": 0.5 * (hl + hr)}[point]
    return float(val @ dx)
