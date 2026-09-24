"""firm.hfvol -- high-frequency volatility and covariance estimators (One Quant Book 4, chapter 21).

Realised variance at any sampling step, subsampling, two-scales realised variance, the Parzen realised kernel,
the pre-averaging estimator, bipower variation, the Hayashi-Yoshida covariance, refresh-time synchronisation,
Roll's spread estimator and the noise-variance estimate. Inputs are log prices on a common clock (one day),
except where observation times are given. NumPy only.

API (stable):
    rv(logp, step=1)                       realised variance from every `step`-th observation
    rv_subsampled(logp, k)                 average of the k offset grids at step k
    noise_variance(logp)                   RV / (2 n): the iid-noise variance estimate
    tsrv(logp, k)                          two-scales realised variance (Zhang, Mykland, Ait-Sahalia)
    realised_kernel(logp, H)               Parzen-kernel realised variance with bandwidth H
    preaveraged(logp, kn)                  pre-averaging estimator with weight g(x) = min(x, 1 - x)
    bipower(logp, step=1)                  (pi / 2) sum |r_i| |r_{i-1}|
    optimal_n(iq, noise_var)               Bandi-Russell sampling count (iq / (4 noise_var^2))^(1/3)
    roll_spread(price)                     2 sqrt(-Cov(dP_t, dP_{t-1})), NaN if the covariance is positive
    hayashi_yoshida(t1, x1, t2, x2)        covariance from overlapping return intervals
    refresh_times(*times)                  times at which every series has traded since the last refresh
    previous_tick(t, x, grid)              last observed value at or before each grid time
"""
from __future__ import annotations

import math

import numpy as np


def rv(logp, step: int = 1) -> float:
    x = np.asarray(logp, dtype=float)[::step]
    return float(np.sum(np.diff(x) ** 2))


def rv_subsampled(logp, k: int) -> float:
    x = np.asarray(logp, dtype=float)
    return float(np.mean([np.sum(np.diff(x[j::k]) ** 2) for j in range(k)]))


def noise_variance(logp) -> float:
    x = np.asarray(logp, dtype=float)
    return rv(x) / (2 * (x.size - 1))


def tsrv(logp, k: int) -> float:
    """Average of the k sparse realised variances minus (n_bar / n) times the all-data realised variance,
    with the small-sample adjustment 1 / (1 - n_bar / n)."""
    x = np.asarray(logp, dtype=float)
    n = x.size - 1
    nbar = (n - k + 1) / k
    return float((rv_subsampled(x, k) - nbar / n * rv(x)) / (1 - nbar / n))


def _parzen(u: np.ndarray) -> np.ndarray:
    a = np.abs(u)
    return np.where(a <= 0.5, 1 - 6 * a**2 + 6 * a**3, np.where(a <= 1, 2 * (1 - a) ** 3, 0.0))


def realised_kernel(logp, H: int) -> float:
    """gamma_0 + sum_{h=1}^{H} k((h - 1) / H) (gamma_h + gamma_{-h}) with Parzen weights."""
    r = np.diff(np.asarray(logp, dtype=float))
    out = float(r @ r)
    for h in range(1, H + 1):
        out += 2 * float(_parzen(np.array([(h - 1) / H]))[0]) * float(r[h:] @ r[:-h])
    return out


def preaveraged(logp, kn: int) -> float:
    """Jacod-Li-Mykland-Podolskij-Vetter: average the returns over windows of kn with weights g(j / kn), square,
    rescale by psi_2, and remove the noise bias with psi_1 (discrete versions of the constants)."""
    r = np.diff(np.asarray(logp, dtype=float))
    n = r.size
    j = np.arange(1, kn)
    g = np.minimum(j / kn, 1 - j / kn)
    ybar = np.convolve(r, g[::-1], mode="valid")                  # sum_j g(j / kn) r_{i + j}
    gg = np.concatenate([[0.0], g, [0.0]])
    psi1 = kn * float(np.sum(np.diff(gg) ** 2))
    psi2 = float(np.sum(g**2)) / kn
    main = n / (n - kn + 2) / (psi2 * kn) * float(ybar @ ybar)
    bias = psi1 / (psi2 * kn * kn) * float(r @ r) / 2
    return main - bias


def bipower(logp, step: int = 1) -> float:
    r = np.abs(np.diff(np.asarray(logp, dtype=float)[::step]))
    return float(math.pi / 2 * np.sum(r[1:] * r[:-1]))


def optimal_n(iq: float, noise_var: float) -> float:
    """Minimiser of 2 IQ / n + (2 n noise_var)^2, the leading terms of the mean squared error of realised variance
    with iid noise (Bandi and Russell)."""
    return (iq / (4 * noise_var**2)) ** (1 / 3)


def roll_spread(price) -> float:
    d = np.diff(np.asarray(price, dtype=float))
    c = float(np.mean((d[1:] - d.mean()) * (d[:-1] - d.mean())))
    return 2 * math.sqrt(-c) if c < 0 else float("nan")


def hayashi_yoshida(t1, x1, t2, x2) -> float:
    """sum over pairs of returns whose intervals (t_{i-1}, t_i] overlap: unbiased for the covariation without
    synchronisation (Hayashi and Yoshida)."""
    t1, x1, t2, x2 = (np.asarray(a, dtype=float) for a in (t1, x1, t2, x2))
    r1, r2 = np.diff(x1), np.diff(x2)
    a1, b1, a2, b2 = t1[:-1], t1[1:], t2[:-1], t2[1:]
    lo = np.searchsorted(b2, a1, side="right")                     # first interval of 2 ending after a1
    hi = np.searchsorted(a2, b1, side="left")                      # intervals of 2 starting before b1
    c2 = np.concatenate([[0.0], np.cumsum(r2)])
    hi = np.maximum(hi, lo)
    return float(np.sum(r1 * (c2[hi] - c2[lo])))


def refresh_times(*times) -> np.ndarray:
    """First time every series has a new observation, then repeatedly after that."""
    ts = [np.asarray(t, dtype=float) for t in times]
    out, cur = [], max(t[0] for t in ts)
    while True:
        out.append(cur)
        nxt = []
        for t in ts:
            k = np.searchsorted(t, cur, side="right")
            if k >= t.size:
                return np.array(out)
            nxt.append(t[k])
        cur = max(nxt)


def previous_tick(t, x, grid) -> np.ndarray:
    t, x = np.asarray(t, dtype=float), np.asarray(x, dtype=float)
    idx = np.searchsorted(t, np.asarray(grid, dtype=float), side="right") - 1
    return x[np.clip(idx, 0, x.size - 1)]
