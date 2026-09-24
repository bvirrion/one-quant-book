"""firm.bayes -- Bayesian updating, shrinkage and MCMC (One Quant Book 4, chapter 14).

Conjugate updaters, empirical-Bayes and James-Stein shrinkage of normal means (for instance the Sharpe
ratios of many managers or signals), a random-walk Metropolis sampler, a Gibbs sampler for the hierarchical
normal model, and the effective-sample-size and R-hat diagnostics. NumPy only.

API (stable):
    beta_binomial(a, b, k, n)                    posterior (a + k, b + n - k)
    normal_normal(m0, v0, xbar, v)               posterior mean and variance of a normal mean
    nig_update(m0, k0, a0, b0, x)                normal-inverse-gamma posterior (m, k, a, b)
    eb_normal_means(x, se)                       empirical-Bayes shrinkage: dict(m, tau2, shrink, post_mean, post_sd)
    james_stein(x, se)                           positive-part James-Stein toward the grand mean
    metropolis(logpdf, x0, n, step, rng)         random-walk Metropolis: (chain, acceptance rate)
    gibbs_hierarchical(x, se, n_iter, rng)       Gibbs sampler for theta_i ~ N(m, tau^2), x_i ~ N(theta_i, se_i^2)
    ess(chain)                                   effective sample size (Geyer's initial positive sequence)
    rhat(chains)                                 Gelman-Rubin potential scale reduction
"""
from __future__ import annotations

import math

import numpy as np


def beta_binomial(a: float, b: float, k: int, n: int) -> tuple[float, float]:
    return a + k, b + n - k


def normal_normal(m0: float, v0: float, xbar: float, v: float) -> tuple[float, float]:
    """Prior N(m0, v0) on a mean, observation xbar ~ N(mean, v): precision-weighted posterior."""
    prec = 1.0 / v0 + 1.0 / v
    return (m0 / v0 + xbar / v) / prec, 1.0 / prec


def nig_update(m0: float, k0: float, a0: float, b0: float, x) -> tuple[float, float, float, float]:
    """x_i ~ N(mu, s2), mu | s2 ~ N(m0, s2 / k0), s2 ~ InvGamma(a0, b0)."""
    x = np.asarray(x, dtype=float)
    n, xbar = x.size, float(x.mean())
    ss = float(np.sum((x - xbar) ** 2))
    kn = k0 + n
    mn = (k0 * m0 + n * xbar) / kn
    return mn, kn, a0 + n / 2, b0 + 0.5 * ss + 0.5 * k0 * n * (xbar - m0) ** 2 / kn


def eb_normal_means(x, se) -> dict:
    """theta_i ~ N(m, tau2), x_i ~ N(theta_i, se_i^2). (m, tau2) by maximum marginal likelihood
    (moments when the se are equal); each x_i shrunk toward m by se_i^2 / (se_i^2 + tau2)."""
    x = np.asarray(x, dtype=float)
    v = np.broadcast_to(np.asarray(se, dtype=float) ** 2, x.shape).astype(float)
    if np.allclose(v, v[0]):
        m = float(x.mean())
        tau2 = max(0.0, float(x.var(ddof=1)) - float(v[0]))
    else:
        tau2 = max(0.0, float(x.var(ddof=1)) - float(v.mean()))
        for _ in range(500):
            w = 1.0 / (v + tau2)
            m = float(np.sum(w * x) / np.sum(w))
            new = max(0.0, float(np.sum(w**2 * ((x - m) ** 2 - v)) / np.sum(w**2)))
            if abs(new - tau2) < 1e-12:
                break
            tau2 = new
        m = float(np.sum(x / (v + tau2)) / np.sum(1.0 / (v + tau2)))
    shrink = v / (v + tau2)
    post_mean = m + (1.0 - shrink) * (x - m)
    post_sd = np.sqrt(v * tau2 / (v + tau2))
    return {"m": m, "tau2": tau2, "shrink": shrink, "post_mean": post_mean, "post_sd": post_sd}


def james_stein(x, se) -> np.ndarray:
    """Positive-part James-Stein toward the grand mean (dimension k >= 4, equal known se)."""
    x = np.asarray(x, dtype=float)
    k = x.size
    xbar = x.mean()
    s = float(np.sum((x - xbar) ** 2))
    c = max(0.0, 1.0 - (k - 3) * float(se) ** 2 / s)
    return xbar + c * (x - xbar)


def metropolis(logpdf, x0, n: int, step, rng: np.random.Generator) -> tuple[np.ndarray, float]:
    """Random-walk Metropolis with Gaussian proposals of standard deviation `step` (scalar or vector)."""
    x = np.atleast_1d(np.asarray(x0, dtype=float)).copy()
    lp = logpdf(x)
    out = np.empty((n, x.size))
    acc = 0
    step = np.broadcast_to(np.asarray(step, dtype=float), x.shape)
    for t in range(n):
        y = x + step * rng.standard_normal(x.size)
        ly = logpdf(y)
        if math.log(rng.random()) < ly - lp:
            x, lp = y, ly
            acc += 1
        out[t] = x
    return out, acc / n


def gibbs_hierarchical(x, se, n_iter: int, rng: np.random.Generator, tau0: float = 0.5) -> dict:
    """Gibbs sampler, flat prior on m and on tau (so tau^2 | rest ~ InvGamma((k - 1) / 2, S / 2))."""
    x = np.asarray(x, dtype=float)
    v = np.broadcast_to(np.asarray(se, dtype=float) ** 2, x.shape).astype(float)
    k = x.size
    tau2 = tau0**2
    m = float(x.mean())
    th_out = np.empty((n_iter, k))
    m_out = np.empty(n_iter)
    tau_out = np.empty(n_iter)
    for t in range(n_iter):
        prec = 1.0 / v + 1.0 / tau2
        theta = (x / v + m / tau2) / prec + rng.standard_normal(k) / np.sqrt(prec)
        m = float(theta.mean() + math.sqrt(tau2 / k) * rng.standard_normal())
        s = float(np.sum((theta - m) ** 2))
        tau2 = (s / 2) / rng.gamma((k - 1) / 2)
        th_out[t], m_out[t], tau_out[t] = theta, m, math.sqrt(tau2)
    return {"theta": th_out, "m": m_out, "tau": tau_out}


def _acf(x: np.ndarray, max_lag: int) -> np.ndarray:
    x = x - x.mean()
    n = x.size
    f = np.fft.rfft(x, 2 * n)
    ac = np.fft.irfft(f * np.conj(f))[: max_lag + 1]
    return ac / ac[0]


def ess(chain) -> float:
    """Effective sample size n / tau, tau = -1 + 2 sum_j (rho_2j + rho_2j+1) summed while the pairs are
    positive (Geyer's initial positive sequence)."""
    x = np.asarray(chain, dtype=float)
    n = x.size
    rho = _acf(x, n - 1)
    tau = -1.0
    for j in range(0, n - 1, 2):
        pair = rho[j] + rho[j + 1]
        if pair < 0:
            break
        tau += 2.0 * pair
    return float(n / max(tau, 1e-12))


def rhat(chains) -> float:
    """Gelman-Rubin statistic for m chains of length n (rows are chains)."""
    c = np.asarray(chains, dtype=float)
    m, n = c.shape
    w = float(np.mean(c.var(axis=1, ddof=1)))
    b = n * float(c.mean(axis=1).var(ddof=1))
    var_plus = (n - 1) / n * w + b / n
    return math.sqrt(var_plus / w)
