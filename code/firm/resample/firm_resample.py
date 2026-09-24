"""firm.resample -- bootstrap, permutation and jackknife (One Quant Book 4, chapter 13).

Index generators for the iid, moving-block and stationary bootstraps (so that one resample of a
multi-column P&L matrix keeps its columns aligned), an automatic block length, percentile intervals,
permutation tests and the jackknife. Seeded, vectorised, NumPy only.

API (stable):
    iid_indices(n, n_boot, rng)                          (n_boot, n) integer array
    block_indices(n, n_boot, block, rng)                 moving blocks of fixed length (circular)
    stationary_indices(n, n_boot, mean_block, rng)       Politis-Romano: geometric block lengths, circular
    optimal_block_length(x)                              (stationary, circular) mean block lengths
    bootstrap(stat, x, idx)                              stat applied to each resample (rows of idx)
    percentile_interval(draws, level=0.95)               (lower, upper)
    permutation_test(stat, x, y, n_perm, rng)            one-sided p-value of stat(x, y) against shuffles of y
    circular_shift_test(stat, x, y, rng, n_shift=None)   the same with circular shifts (keeps y's dependence)
    jackknife(stat, x)                                   dict(estimate, bias_corrected, bias, se)
"""
from __future__ import annotations

import math

import numpy as np


def iid_indices(n: int, n_boot: int, rng: np.random.Generator) -> np.ndarray:
    return rng.integers(0, n, size=(n_boot, n))


def block_indices(n: int, n_boot: int, block: int, rng: np.random.Generator) -> np.ndarray:
    """Moving-block bootstrap (Kunsch): concatenate blocks of `block` consecutive days, wrapping at the end."""
    k = -(-n // block)
    starts = rng.integers(0, n, size=(n_boot, k))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(n_boot, k * block)[:, :n]
    return idx % n


def stationary_indices(n: int, n_boot: int, mean_block: float, rng: np.random.Generator) -> np.ndarray:
    """Stationary bootstrap (Politis-Romano): each day starts a new block with probability 1 / mean_block,
    at a uniform position; otherwise it continues the current block, wrapping circularly."""
    p = 1.0 / max(1.0, mean_block)
    idx = np.empty((n_boot, n), dtype=np.int64)
    idx[:, 0] = rng.integers(0, n, n_boot)
    new = rng.random((n_boot, n)) < p
    jumps = rng.integers(0, n, size=(n_boot, n))
    for t in range(1, n):
        idx[:, t] = np.where(new[:, t], jumps[:, t], (idx[:, t - 1] + 1) % n)
    return idx


def _flat_top(t: np.ndarray) -> np.ndarray:
    a = np.abs(t)
    return np.where(a <= 0.5, 1.0, np.where(a <= 1.0, 2.0 * (1.0 - a), 0.0))


def optimal_block_length(x) -> tuple[float, float]:
    """Automatic mean block length for the stationary and circular bootstraps: Politis and White (2004)
    with the constants corrected by Patton, Politis and White (2009). The bandwidth M is twice the first
    lag after which K_n consecutive autocorrelations are insignificant."""
    x = np.asarray(x, dtype=float)
    n = x.size
    xc = x - x.mean()
    k_n = max(5, int(math.ceil(math.sqrt(math.log10(n)))))
    m_max = int(math.ceil(math.sqrt(n))) + k_n
    acov = np.array([xc[: n - k] @ xc[k:] / n for k in range(m_max + 1)])
    rho = acov / acov[0]
    crit = 2.0 * math.sqrt(math.log10(n) / n)
    m_hat = m_max - k_n
    for m in range(1, m_max - k_n + 1):
        if np.all(np.abs(rho[m: m + k_n]) < crit):
            m_hat = m - 1
            break
    big_m = min(2 * max(m_hat, 1), m_max)
    k = np.arange(-big_m, big_m + 1)
    lam = _flat_top(k / big_m)
    r = acov[np.abs(k)]
    g = float(np.sum(lam * np.abs(k) * r))
    s0 = float(np.sum(lam * r))
    if g == 0.0:
        return 1.0, 1.0
    b_sb = (2.0 * g * g / (2.0 * s0 * s0)) ** (1 / 3) * n ** (1 / 3)
    b_cb = (2.0 * g * g / (4.0 / 3.0 * s0 * s0)) ** (1 / 3) * n ** (1 / 3)
    cap = math.ceil(min(3 * math.sqrt(n), n / 3))
    return float(min(max(b_sb, 1.0), cap)), float(min(max(b_cb, 1.0), cap))


def bootstrap(stat, x, idx: np.ndarray) -> np.ndarray:
    """Apply stat (a function of an array whose first axis is time) to every resample."""
    x = np.asarray(x)
    return np.array([stat(x[row]) for row in idx])


def percentile_interval(draws, level: float = 0.95) -> tuple[float, float]:
    a = (1.0 - level) / 2.0
    lo, hi = np.quantile(np.asarray(draws, dtype=float), [a, 1.0 - a])
    return float(lo), float(hi)


def permutation_test(stat, x, y, n_perm: int, rng: np.random.Generator) -> float:
    """One-sided p-value of stat(x, y) against stat(x, y permuted); exact under exchangeability of y.
    The observed arrangement counts as one of the permutations, so the p-value is never zero."""
    x, y = np.asarray(x), np.asarray(y)
    t0 = stat(x, y)
    hits = sum(stat(x, y[rng.permutation(y.size)]) >= t0 for _ in range(n_perm))
    return (1 + hits) / (1 + n_perm)


def circular_shift_test(stat, x, y, rng: np.random.Generator, n_shift: int | None = None) -> float:
    """As permutation_test, but y is rotated by a random offset: its own serial dependence survives."""
    x, y = np.asarray(x), np.asarray(y)
    n = y.size
    t0 = stat(x, y)
    shifts = np.arange(1, n) if n_shift is None else rng.integers(1, n, n_shift)
    hits = sum(stat(x, np.roll(y, int(s))) >= t0 for s in shifts)
    return (1 + hits) / (1 + len(shifts))


def jackknife(stat, x) -> dict:
    """Leave-one-out jackknife: bias (n - 1)(mean of leave-one-out - full), bias-corrected estimate, and se."""
    x = np.asarray(x)
    n = x.shape[0]
    full = float(stat(x))
    loo = np.array([stat(np.delete(x, i, axis=0)) for i in range(n)], dtype=float)
    bias = (n - 1) * (loo.mean() - full)
    se = math.sqrt((n - 1) / n * float(np.sum((loo - loo.mean()) ** 2)))
    return {"estimate": full, "bias": bias, "bias_corrected": full - bias, "se": se}
