"""firm.abtest -- live experiments on the firm's own flow (build of One Quant Book 7, chapter 21).

Deterministic hash assignment of randomisation units (orders, days, stock-days) to arms, the difference in means and
its standard error, CUPED (a regression adjustment on covariates the treatment cannot affect), post-stratification,
the cluster-level estimate for a randomisation unit coarser than the observation, power, the minimum detectable effect
and the sample size, the sample-ratio-mismatch check, and the mixture sequential probability ratio test with its
always-valid p-value (Johari, Koomen, Pekelis and Walsh). NumPy and the standard library only.

API (stable):
    bucket(unit, experiment, salt)            uniform [0, 1) from SHA-256 of 'experiment:salt:unit'
    assign(units, experiment, share, salt)    bool array, True = treatment; the same unit always gets the same arm
    diff_means(y, t)                          (treatment mean - control mean, Welch standard error)
    cuped(y, X, t)                            (estimate, se, theta): y - (X - mean X) theta, theta by pooled OLS
    stratified(y, t, strata)                  (estimate, se): stratum differences weighted by stratum share
    cluster_diff(y, t, cluster)               (estimate, se) when whole clusters are assigned: cluster-robust se
    demean_by(v, group)                       v minus its group mean (a day's common shock removed)
    power(effect, se, alpha)                  two-sided power of the z-test
    mde(se, alpha, power)                     minimum detectable effect
    sample_size(effect, sd, alpha, power, share)  units needed in total
    srm_pvalue(n_t, n_c, share)               p-value of the observed split against the planned share
    msprt(d, se, tau)                         mixture likelihood ratio of an estimate against zero, N(0, tau^2) mixing
    always_valid_p(d, se, tau)                running min(1, 1 / Lambda) over looks (the last axis)
"""
from __future__ import annotations

import hashlib
import math
from statistics import NormalDist

import numpy as np

_N = NormalDist()


def bucket(unit, experiment: str, salt: str = "") -> float:
    h = hashlib.sha256(f"{experiment}:{salt}:{unit}".encode()).digest()
    return int.from_bytes(h[:8], "big") / 2.0**64


def assign(units, experiment: str, share: float = 0.5, salt: str = "") -> np.ndarray:
    return np.array([bucket(u, experiment, salt) < share for u in units], dtype=bool)


def diff_means(y, t):
    y, t = np.asarray(y, float), np.asarray(t, bool)
    a, b = y[t], y[~t]
    d = a.mean() - b.mean()
    return float(d), math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


def cuped(y, X, t):
    """Regress y on the covariates pooled over both arms, then compare the adjusted outcomes. The covariates must be
    unaffected by the treatment (measured before assignment, or outside the firm's reach)."""
    y = np.asarray(y, float)
    X = np.asarray(X, float).reshape(len(y), -1)
    Xc = X - X.mean(axis=0)
    theta = np.linalg.lstsq(Xc, y - y.mean(), rcond=None)[0]
    d, se = diff_means(y - Xc @ theta, t)
    return d, se, theta


def stratified(y, t, strata):
    y, t, strata = np.asarray(y, float), np.asarray(t, bool), np.asarray(strata)
    d = v = 0.0
    for s in np.unique(strata):
        m = strata == s
        w = m.mean()
        a, b = y[m & t], y[m & ~t]
        d += w * (a.mean() - b.mean())
        v += w * w * (a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float(d), math.sqrt(v)


def cluster_diff(y, t, cluster):
    """Order-weighted difference in means when whole clusters are assigned, with a cluster-robust standard error:
    each arm's mean is a ratio of cluster totals, linearised per cluster."""
    y, t, cluster = np.asarray(y, float), np.asarray(t, bool), np.asarray(cluster)
    _, inv = np.unique(cluster, return_inverse=True)
    n = np.bincount(inv).astype(float)
    tot = np.bincount(inv, weights=y)
    arm = np.bincount(inv, weights=t) / n
    if np.any((arm > 0) & (arm < 1)):
        raise ValueError("an arm must be constant within each cluster")
    mean, var = [], 0.0
    for m in (arm > 0.5, arm < 0.5):
        mu = tot[m].sum() / n[m].sum()
        e = tot[m] - mu * n[m]
        k = int(m.sum())
        mean.append(mu)
        var += k / (k - 1) * float((e * e).sum()) / n[m].sum() ** 2
    return float(mean[0] - mean[1]), math.sqrt(var)


def demean_by(v, group):
    """Subtract each group's mean (stratification by the group when assignment is balanced within it)."""
    v = np.asarray(v, float)
    _, inv = np.unique(np.asarray(group), return_inverse=True)
    return v - (np.bincount(inv, weights=v) / np.bincount(inv))[inv]


def power(effect: float, se: float, alpha: float = 0.05) -> float:
    z, k = _N.inv_cdf(1 - alpha / 2), abs(effect) / se
    return _N.cdf(k - z) + _N.cdf(-k - z)


def mde(se: float, alpha: float = 0.05, power: float = 0.8) -> float:
    return (_N.inv_cdf(1 - alpha / 2) + _N.inv_cdf(power)) * se


def sample_size(effect: float, sd: float, alpha: float = 0.05, power: float = 0.8, share: float = 0.5) -> float:
    k = (_N.inv_cdf(1 - alpha / 2) + _N.inv_cdf(power)) * sd / abs(effect)
    return k * k * (1 / share + 1 / (1 - share))


def srm_pvalue(n_t: int, n_c: int, share: float = 0.5) -> float:
    n = n_t + n_c
    z = (n_t - share * n) / math.sqrt(n * share * (1 - share))
    return 2 * (1 - _N.cdf(abs(z)))


def msprt(d, se, tau: float):
    """Lambda = sqrt(V / (V + tau^2)) exp(tau^2 d^2 / (2 V (V + tau^2))), V = se^2: the likelihood ratio of the
    estimate d under a N(0, tau^2) mixture of effects against the null of no effect."""
    d, V = np.asarray(d, float), np.asarray(se, float) ** 2
    return np.sqrt(V / (V + tau * tau)) * np.exp(tau * tau * d * d / (2 * V * (V + tau * tau)))


def always_valid_p(d, se, tau: float):
    return np.minimum.accumulate(np.minimum(1.0, 1.0 / msprt(d, se, tau)), axis=-1)
