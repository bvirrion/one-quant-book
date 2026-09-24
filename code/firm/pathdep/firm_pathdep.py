"""Path-dependent payoffs on a common path interface (build of Book 5, Chapter 16).

A path set is an array of shape (n_paths, n_dates + 1): column 0 is today's spot, the others the spot at the
fixing (or monitoring) dates. Payoff functions read only that array, so the same payoff is priced under any
model that produces paths (Black-Scholes here; local volatility and Heston in their own components).
Closed forms: the discrete geometric Asian (the control variate of Kemna and Vorst), the continuous floating-strike
lookback call (Goldman, Sosin and Gatto), the Black-Scholes forward-start option.
"""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "bs"))
from firm_bs import bs, ncdf  # noqa: E402

BGK_BETA = 0.5826


# ---------------------------------------------------------------- paths
def gbm_paths(s: float, times, r: float, q: float, vol: float, n_paths: int, seed: int) -> np.ndarray:
    """Exact Black-Scholes paths at the given increasing times (antithetic pairs)."""
    times = np.asarray(times, float)
    dt = np.diff(np.concatenate([[0.0], times]))
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((n_paths // 2, len(times)))
    z = np.vstack([z, -z])
    logs = np.cumsum((r - q - 0.5 * vol * vol) * dt + vol * np.sqrt(dt) * z, axis=1)
    return np.hstack([np.full((len(z), 1), s), s * np.exp(logs)])


# ---------------------------------------------------------------- Asians
def asian_payoff(paths: np.ndarray, strike: float, right: str = "C", geometric: bool = False) -> np.ndarray:
    """Average over the fixing dates (columns 1..n), fixed strike."""
    fix = paths[:, 1:]
    avg = np.exp(np.mean(np.log(fix), axis=1)) if geometric else np.mean(fix, axis=1)
    return np.maximum(avg - strike, 0.0) if right == "C" else np.maximum(strike - avg, 0.0)


def geometric_asian(s: float, k: float, t: float, r: float, q: float, vol: float, n: int, right: str = "C") -> float:
    """Discrete geometric-average option, fixings at t i / n, i = 1..n: ln G is normal."""
    mean = math.log(s) + (r - q - 0.5 * vol * vol) * t * (n + 1) / (2 * n)
    var = vol * vol * t * (n + 1) * (2 * n + 1) / (6 * n * n)
    fwd = math.exp(mean + 0.5 * var)
    sd = math.sqrt(var)
    d1 = (math.log(fwd / k) + 0.5 * var) / sd
    d2 = d1 - sd
    if right == "C":
        return math.exp(-r * t) * (fwd * ncdf(d1) - k * ncdf(d2))
    return math.exp(-r * t) * (k * ncdf(-d2) - fwd * ncdf(-d1))


def asian_mc(s: float, k: float, t: float, r: float, q: float, vol: float, n: int, n_paths: int = 100_000,
             seed: int = 16, right: str = "C") -> dict:
    """Arithmetic Asian by Monte Carlo, plain and with the geometric Asian as control variate (the coefficient
    estimated by regression on the same paths)."""
    times = t * np.arange(1, n + 1) / n
    p = gbm_paths(s, times, r, q, vol, n_paths, seed)
    disc = math.exp(-r * t)
    a = disc * asian_payoff(p, k, right)
    g = disc * asian_payoff(p, k, right, geometric=True)
    exact_g = geometric_asian(s, k, t, r, q, vol, n, right)
    c = np.cov(a, g)
    beta = c[0, 1] / c[1, 1]
    adj = a - beta * (g - exact_g)
    m = len(a)
    corr = c[0, 1] / math.sqrt(c[0, 0] * c[1, 1])
    return {"plain": float(a.mean()), "plain_se": float(a.std() / math.sqrt(m)), "cv": float(adj.mean()),
            "cv_se": float(adj.std() / math.sqrt(m)), "beta": float(beta), "corr": float(corr), "geometric": exact_g}


# ---------------------------------------------------------------- lookbacks
def lookback_floating_call(s: float, s_min: float, t: float, r: float, q: float, vol: float) -> float:
    """Continuously monitored floating-strike lookback call paying S_T - min S (carry b = r - q, b != 0)."""
    b = r - q
    sv = vol * math.sqrt(t)
    a1 = (math.log(s / s_min) + (b + 0.5 * vol * vol) * t) / sv
    a2 = a1 - sv
    term = s * math.exp(-r * t) * vol * vol / (2 * b) * (
        (s / s_min) ** (-2 * b / (vol * vol)) * ncdf(-a1 + 2 * b * math.sqrt(t) / vol) - math.exp(b * t) * ncdf(-a1))
    return s * math.exp((b - r) * t) * ncdf(a1) - s_min * math.exp(-r * t) * ncdf(a2) + term


def lookback_payoff(paths: np.ndarray, right: str = "C") -> np.ndarray:
    """Floating strike, extremes over all columns including today's spot."""
    if right == "C":
        return paths[:, -1] - paths.min(axis=1)
    return paths.max(axis=1) - paths[:, -1]


def lookback_shifted(s: float, t: float, r: float, q: float, vol: float, n: int) -> float:
    """Discretely monitored (n dates) floating lookback call from the continuous one, by moving the extreme as
    the barrier shift moves a barrier: the monitored minimum is taken as e^(beta sigma sqrt(dt)) times the true
    one, so C_d = e^(x) C_c - (e^(x) - 1) S e^(-qT), x = beta sigma sqrt(T / n). An approximation, checked
    against simulation in the tests."""
    x = math.exp(BGK_BETA * vol * math.sqrt(t / n))
    return x * lookback_floating_call(s, s, t, r, q, vol) - (x - 1) * s * math.exp(-q * t)


# ---------------------------------------------------------------- forward starts and cliquets
def forward_start_call(s: float, k_rel: float, t1: float, t: float, r: float, q: float, vol: float) -> float:
    """Call struck at k_rel S_(t1), expiring at t: by homogeneity, S e^(-q t1) BS(1, k_rel, t - t1)."""
    return s * math.exp(-q * t1) * bs(1.0, k_rel, t - t1, r, q, vol, "C")


def period_returns(paths: np.ndarray) -> np.ndarray:
    """Returns between consecutive columns: S_i / S_(i-1) - 1."""
    return paths[:, 1:] / paths[:, :-1] - 1


def cliquet_payoff(paths: np.ndarray, local_floor: float = -math.inf, local_cap: float = math.inf,
                   global_floor: float = -math.inf, global_cap: float = math.inf) -> np.ndarray:
    """Sum of the period returns, each clipped to [local_floor, local_cap], then the sum clipped globally."""
    clipped = np.clip(period_returns(paths), local_floor, local_cap)
    return np.clip(clipped.sum(axis=1), global_floor, global_cap)


def reverse_cliquet_payoff(paths: np.ndarray, coupon: float) -> np.ndarray:
    """max(0, coupon + sum of the negative period returns): the coupon is eroded by every fall."""
    return np.maximum(0.0, coupon + np.minimum(period_returns(paths), 0.0).sum(axis=1))


def forward_smile_from_paths(paths: np.ndarray, i1: int, i2: int, tau: float, ks) -> np.ndarray:
    """Implied volatilities (Black, zero rates) of forward-start calls on S_(i2) / S_(i1) from simulated paths."""
    from firm_bs import implied_vol
    ratio = paths[:, i2] / paths[:, i1]
    out = []
    for k in ks:
        right = "C" if k >= 1 else "P"
        pay = np.maximum(ratio - k, 0) if right == "C" else np.maximum(k - ratio, 0)
        out.append(implied_vol(float(pay.mean()), 1.0, k, tau, 1.0, right))
    return np.array(out)
