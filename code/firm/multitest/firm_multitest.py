"""firm.multitest -- multiple-testing corrections (One Quant Book 4, chapter 12).

Adjusted p-values for a family of tests, max-statistic p-values that respect the correlation between
the tests (by Gaussian simulation, or from any matrix of null draws such as the bootstrap of chapter 13),
the effective number of independent trials a search amounts to, and the deflated Sharpe ratio.
NumPy only.

API (stable):
    norm_cdf(x), norm_ppf(p)                    standard normal cdf and quantile
    bonferroni(p), holm(p)                      family-wise error rate adjusted p-values
    benjamini_hochberg(p), benjamini_yekutieli(p)   false discovery rate adjusted p-values
    maxt_pvalues(t, corr=None, n_sim, seed, null_draws=None, stepdown=False)
                                                one-sided max-statistic adjusted p-values
    effective_trials(p_single, p_family)        N with 1 - (1 - p_single)^N = p_family
    expected_max_sr(n_trials, sr_var)           expected maximum of n_trials null Sharpe ratios
    deflated_sharpe(sr, n_obs, skew, kurt, sr0) probability the true Sharpe ratio exceeds sr0
"""
from __future__ import annotations

import math

import numpy as np

EULER_GAMMA = 0.5772156649015329


def norm_cdf(x):
    x = np.asarray(x, dtype=float)
    return 0.5 * np.vectorize(math.erfc)(-x / math.sqrt(2.0))


def _ppf_scalar(p: float) -> float:
    if not 0.0 < p < 1.0:
        return -math.inf if p <= 0.0 else math.inf
    lo, hi = -40.0, 40.0
    x = 0.0
    for _ in range(200):                                   # bisection, then Newton polish
        x = 0.5 * (lo + hi)
        if 0.5 * math.erfc(-x / math.sqrt(2.0)) < p:
            lo = x
        else:
            hi = x
        if hi - lo < 1e-10:
            break
    for _ in range(3):
        f = 0.5 * math.erfc(-x / math.sqrt(2.0)) - p
        x -= f / (math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi))
    return x


def norm_ppf(p):
    out = np.vectorize(_ppf_scalar)(np.asarray(p, dtype=float))
    return float(out) if out.ndim == 0 else out


def _check(p) -> np.ndarray:
    p = np.asarray(p, dtype=float)
    if p.ndim != 1 or np.any((p < 0) | (p > 1)):
        raise ValueError("p must be a 1-d array of probabilities")
    return p


def bonferroni(p) -> np.ndarray:
    p = _check(p)
    return np.minimum(1.0, p.size * p)


def holm(p) -> np.ndarray:
    """Step-down: the k-th smallest p-value (k = 1..m) is multiplied by m - k + 1, then made monotone."""
    p = _check(p)
    m = p.size
    order = np.argsort(p)
    adj = np.maximum.accumulate((m - np.arange(m)) * p[order])
    out = np.empty(m)
    out[order] = np.minimum(1.0, adj)
    return out


def benjamini_hochberg(p, dependence_factor: float = 1.0) -> np.ndarray:
    """Step-up: the k-th smallest p-value is multiplied by m / k, then made monotone from the top."""
    p = _check(p)
    m = p.size
    order = np.argsort(p)
    ranked = p[order] * m * dependence_factor / np.arange(1, m + 1)
    adj = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.minimum(1.0, adj)
    return out


def benjamini_yekutieli(p) -> np.ndarray:
    """Benjamini-Hochberg with the harmonic factor sum 1/k: valid under any dependence."""
    m = _check(p).size
    return benjamini_hochberg(p, dependence_factor=float(np.sum(1.0 / np.arange(1, m + 1))))


def _gaussian_null(corr: np.ndarray, n_sim: int, seed: int) -> np.ndarray:
    w, v = np.linalg.eigh(0.5 * (corr + corr.T))
    root = v * np.sqrt(np.clip(w, 0.0, None))
    rng = np.random.default_rng(seed)
    out = np.empty((n_sim, corr.shape[0]))
    for a in range(0, n_sim, 10_000):                      # blocks keep memory flat
        b = min(n_sim, a + 10_000)
        out[a:b] = rng.standard_normal((b - a, corr.shape[0])) @ root.T
    return out


def maxt_pvalues(t, corr=None, n_sim: int = 100_000, seed: int = 0, null_draws=None,
                 stepdown: bool = False) -> np.ndarray:
    """One-sided max-statistic adjusted p-values: P(max_j Z_j >= t_i) under the joint null.

    The null is Gaussian with correlation `corr` (identity if None), or the rows of `null_draws`
    (n_sim x m, e.g. bootstrap statistics centred on the null). With stepdown=True the maximum for the
    k-th largest statistic runs over the hypotheses not yet rejected (Romano-Wolf), which is uniformly
    less conservative and still controls the family-wise error rate.
    """
    t = np.asarray(t, dtype=float)
    m = t.size
    if null_draws is None:
        null_draws = _gaussian_null(np.eye(m) if corr is None else np.asarray(corr, float), n_sim, seed)
    null_draws = np.asarray(null_draws, dtype=float)
    if not stepdown:
        mx = np.sort(null_draws.max(axis=1))
        return 1.0 - np.searchsorted(mx, t, side="left") / mx.size
    order = np.argsort(-t)
    adj = np.empty(m)
    for k, i in enumerate(order):
        mx = null_draws[:, order[k:]].max(axis=1)
        adj[k] = np.mean(mx >= t[i])
    adj = np.maximum.accumulate(adj)
    out = np.empty(m)
    out[order] = adj
    return out


def effective_trials(p_single: float, p_family: float) -> float:
    """The number N of independent trials whose best would be as surprising: 1 - (1 - p)^N = p_family."""
    if not 0.0 < p_single < 1.0 or not 0.0 < p_family < 1.0:
        raise ValueError("p-values must lie in (0, 1)")
    return math.log1p(-p_family) / math.log1p(-p_single)


def expected_max_sr(n_trials: float, sr_var: float) -> float:
    """Expected maximum of n_trials independent N(0, sr_var) Sharpe ratios (Bailey and Lopez de Prado)."""
    if n_trials <= 1:
        return 0.0
    z1 = norm_ppf(1.0 - 1.0 / n_trials)
    z2 = norm_ppf(1.0 - 1.0 / (n_trials * math.e))
    return math.sqrt(sr_var) * ((1.0 - EULER_GAMMA) * z1 + EULER_GAMMA * z2)


def deflated_sharpe(sr: float, n_obs: int, skew: float = 0.0, kurt: float = 3.0, sr0: float = 0.0) -> float:
    """Probability that the true per-period Sharpe ratio exceeds sr0, given the estimate sr from n_obs
    returns with the given skewness and (non-excess) kurtosis. With sr0 = expected_max_sr(N, V) it is the
    deflated Sharpe ratio; with sr0 = 0, the probabilistic Sharpe ratio."""
    den = math.sqrt(max(1e-300, 1.0 - skew * sr + 0.25 * (kurt - 1.0) * sr * sr))
    return float(norm_cdf((sr - sr0) * math.sqrt(n_obs - 1) / den))
