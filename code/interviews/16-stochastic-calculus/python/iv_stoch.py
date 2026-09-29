"""Book 18, chapter 16: stochastic calculus answers (closed forms, sympy, and Monte Carlo checks)."""
from math import exp, log, sqrt

import numpy as np
import sympy as sp
from scipy.stats import norm


def ito_drift(f_expr, w):
    """Drift of f(W_t) by Ito: (1/2) f''."""
    return sp.Rational(1, 2) * sp.diff(f_expr, w, 2)


def exit_prob_up(a, b, mu=0.0, sigma=1.0):
    """X = mu t + sigma W from 0: probability of hitting +a before -b."""
    if mu == 0:
        return b / (a + b)
    k = 2 * mu / sigma**2
    return (1 - exp(k * b)) / (exp(-k * a) - exp(k * b))


def max_tail(a, t=1.0):
    """P(max_{s<=t} W_s >= a) = 2 P(W_t >= a) (reflection principle)."""
    return 2 * norm.sf(a / sqrt(t))


def simulate_max_tail(a, n_steps, paths, seed, t=1.0):
    rng = np.random.default_rng(seed)
    dt = t / n_steps
    w = np.zeros(paths)
    m = np.zeros(paths)
    for _ in range(n_steps):
        w += sqrt(dt) * rng.standard_normal(paths)
        np.maximum(m, w, out=m)
    return float(np.mean(m >= a))


def both_positive(t1=1.0, t2=2.0):
    """P(W_t1 > 0, W_t2 > 0) = 1/4 + arcsin(rho)/(2 pi), rho = sqrt(t1/t2)."""
    rho = sqrt(t1 / t2)
    return 0.25 + np.arcsin(rho) / (2 * np.pi)


def gbm_mean_median(mu, sigma, t):
    return exp(mu * t), exp((mu - sigma * sigma / 2) * t)


def digital_prices(s, k, sigma, t, r=0.0):
    d1 = (log(s / k) + (r + sigma * sigma / 2) * t) / (sigma * sqrt(t))
    d2 = d1 - sigma * sqrt(t)
    return exp(-r * t) * norm.cdf(d2), s * norm.cdf(d1)
