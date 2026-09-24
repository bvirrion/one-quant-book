"""Book 4, chapter 13: resampling (teaching module).

A volatility-selling strategy: each day it earns a premium and pays the day's squared return. Its P&L
inherits the clustering of volatility, so days are not independent, and the iid bootstrap interval for its
Sharpe ratio is too narrow; block bootstraps that keep the clusters together repair much of it.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3] / "firm" / "resample"))
from firm_resample import (  # noqa: E402
    block_indices,
    circular_shift_test,
    iid_indices,
    jackknife,
    optimal_block_length,
    percentile_interval,
    permutation_test,
    stationary_indices,
)

N_DAYS = 1260          # five years
SR_ANNUAL = 1.1        # population Sharpe ratio of the strategy
PHI = 0.9              # daily AR(1) coefficient of log volatility
SLV = 0.4              # stationary standard deviation of log volatility


def pnl_sd(phi: float = PHI, slv: float = SLV) -> float:
    """Population standard deviation of 1 - r^2 with r = vol * eps, vol = exp(h - slv^2): 3 exp(4 slv^2) - 1."""
    return math.sqrt(3 * math.exp(4 * slv**2) - 1)


def pnl_lrv_factor(phi: float = PHI, slv: float = SLV, kmax: int = 5000) -> float:
    """Long-run variance over variance: Cov(r_t^2, r_{t+k}^2) = exp(4 slv^2 phi^k) - 1 for k >= 1."""
    k = np.arange(1, kmax + 1)
    cov = np.exp(4 * slv**2 * phi**k) - 1
    return float(1 + 2 * cov.sum() / pnl_sd(phi, slv) ** 2)


def strategy(seed: int, n: int = N_DAYS, phi: float = PHI, slv: float = SLV) -> np.ndarray:
    """Daily P&L of selling one day's variance, in units of the average daily variance."""
    rng = np.random.default_rng(seed)
    h = np.empty(n)
    h[0] = slv * rng.standard_normal()
    e = rng.standard_normal(n)
    sd = slv * math.sqrt(1 - phi**2)
    for t in range(1, n):
        h[t] = phi * h[t - 1] + sd * e[t]
    r = np.exp(h - slv**2) * rng.standard_normal(n)
    return SR_ANNUAL / math.sqrt(252) * pnl_sd(phi, slv) + 1 - r**2


def market(seed: int, n: int = N_DAYS, phi: float = PHI, slv: float = SLV) -> np.ndarray:
    """The daily returns behind strategy(seed) (same draws), for the permutation example."""
    rng = np.random.default_rng(seed)
    h = np.empty(n)
    h[0] = slv * rng.standard_normal()
    e = rng.standard_normal(n)
    sd = slv * math.sqrt(1 - phi**2)
    for t in range(1, n):
        h[t] = phi * h[t - 1] + sd * e[t]
    return np.exp(h - slv**2) * rng.standard_normal(n)


def sharpe(x) -> float:
    x = np.asarray(x)
    return float(x.mean() / x.std(ddof=1) * math.sqrt(252))


def sharpe_rows(xb: np.ndarray) -> np.ndarray:
    return xb.mean(axis=1) / xb.std(axis=1, ddof=1) * math.sqrt(252)


def intervals(x: np.ndarray, n_boot: int = 1000, seed: int = 0, block: float | None = None) -> dict:
    """95% percentile intervals for the Sharpe ratio: iid, moving-block and stationary bootstraps."""
    rng = np.random.default_rng(seed)
    n = x.size
    b_sb, b_cb = optimal_block_length(x) if block is None else (block, block)
    out = {"b_sb": b_sb, "b_cb": b_cb}
    for name, idx in (("iid", iid_indices(n, n_boot, rng)),
                      ("block", block_indices(n, n_boot, max(1, round(b_cb)), rng)),
                      ("stationary", stationary_indices(n, n_boot, b_sb, rng))):
        draws = sharpe_rows(x[idx])
        out[name] = percentile_interval(draws)
        out[name + "_se"] = float(draws.std(ddof=1))
        out[name + "_draws"] = draws
    return out


def coverage(n_hist: int = 400, n_boot: int = 500, seed0: int = 1000, block: float | None = None,
             phi: float = PHI, slv: float = SLV) -> dict:
    """Share of simulated histories whose 95% interval contains the true Sharpe ratio (integer counts)."""
    hits = {"iid": 0, "block": 0, "stationary": 0}
    blocks = []
    for k in range(n_hist):
        x = strategy(seed0 + k, phi=phi, slv=slv)
        iv = intervals(x, n_boot=n_boot, seed=seed0 + k, block=block)
        blocks.append(iv["b_sb"])
        for name in hits:
            lo, hi = iv[name]
            hits[name] += int(lo <= SR_ANNUAL <= hi)
    return {"hits": hits, "n": n_hist, "pct": {k: 100 * v / n_hist for k, v in hits.items()},
            "median_block": float(np.median(blocks))}


def sampling_sd(n_hist: int = 4000, seed0: int = 50_000, n: int = N_DAYS) -> float:
    """Monte Carlo standard deviation of the five-year Sharpe ratio across histories (the truth)."""
    return float(np.std([sharpe(strategy(seed0 + k, n=n)) for k in range(n_hist)], ddof=1))


def se_by_block(blocks=(1, 2, 5, 10, 20, 40, 60, 90, 120), n_hist: int = 60, n_boot: int = 400, seed0: int = 7000):
    """Average stationary-bootstrap standard error of the Sharpe ratio against the mean block length."""
    out = []
    for b in blocks:
        ses = []
        for k in range(n_hist):
            x = strategy(seed0 + k)
            idx = stationary_indices(x.size, n_boot, b, np.random.default_rng(seed0 + k))
            ses.append(sharpe_rows(x[idx]).std(ddof=1))
        out.append((b, float(np.mean(ses))))
    return out


def problem(seed: int = 2213, n_boot: int = 4000) -> dict:
    x = strategy(seed)
    iv = intervals(x, n_boot=n_boot, seed=1)
    z = (x - x.mean()) / x.std()
    rho = [float(np.corrcoef(x[k:], x[:-k])[0, 1]) for k in (1, 5, 20)]
    jk = jackknife(lambda v: v.mean() / v.std(ddof=1) * math.sqrt(252), x)
    sr1 = sharpe(x) / math.sqrt(252)
    return {"sr": sharpe(x), "kurt": float(np.mean(z**4)), "rho": rho, "b_sb": iv["b_sb"], "b_cb": iv["b_cb"],
            "iid": iv["iid"], "block": iv["block"], "stationary": iv["stationary"],
            "iid_se": iv["iid_se"], "block_se": iv["block_se"], "stationary_se": iv["stationary_se"],
            "iid_draws": iv["iid_draws"], "stationary_draws": iv["stationary_draws"],
            "jack_se": jk["se"], "jack_bias": jk["bias"],
            "skew": float(np.mean(z**3)),
            "delta_se": math.sqrt((1 - np.mean(z**3) * sr1 + 0.25 * (np.mean(z**4) - 1) * sr1**2) / x.size)
            * math.sqrt(252)}


# --- permutation tests: two independent histories, a persistent signal ---------------------------------

def signal(seed: int, window: int = 20) -> np.ndarray:
    """Trailing `window`-day mean squared return of an independent market, known before each day."""
    r2 = market(seed) ** 2
    c = np.concatenate([[0.0], np.cumsum(r2)])
    s = np.empty(r2.size)
    for t in range(r2.size):
        a = max(0, t - window)
        s[t] = (c[t] - c[a]) / max(1, t - a) if t > 0 else 1.0
    return s


def _corr(a, b) -> float:
    return float(np.corrcoef(a, b)[0, 1])


def spurious_rejections(n_pairs: int = 200, n_perm: int = 199, seed0: int = 300) -> dict:
    """Rejection rates at 5% of the permutation and circular-shift tests of |correlation| between a strategy's
    P&L and a signal built from an independent market: every rejection is false."""
    rng = np.random.default_rng(seed0)
    perm = shift = 0
    for k in range(n_pairs):
        x, s = strategy(seed0 + 2 * k), signal(seed0 + 2 * k + 1)

        def stat(a, b):
            return abs(_corr(a, b))

        perm += int(permutation_test(stat, s, x, n_perm, rng) <= 0.05)
        shift += int(circular_shift_test(stat, s, x, rng, n_shift=n_perm) <= 0.05)
    return {"perm": perm / n_pairs, "shift": shift / n_pairs, "n": n_pairs}


# --- bootstrapping the reality check of chapter 12 -------------------------------------------------------

def reality_check(n_boot: int = 2000, seed: int = 3) -> dict:
    """Stationary-bootstrap max-t p-value of the best of chapter 12's two hundred momentum rules."""
    sys.path.insert(0, str(HERE.parents[2] / "12-testing-and-multiple-testing" / "python"))
    from qm_testing import SEED, tstats, variants
    sys.path.insert(0, str(HERE.parents[3] / "firm" / "multitest"))
    from firm_multitest import maxt_pvalues

    pnl = variants(SEED)
    t = tstats(pnl)
    n = pnl.shape[0]
    b_sb = float(np.median([optimal_block_length(pnl[:, j])[0] for j in range(0, pnl.shape[1], 20)]))
    idx = stationary_indices(n, n_boot, b_sb, np.random.default_rng(seed))
    mu, sd = pnl.mean(0), pnl.std(0, ddof=1)
    draws = np.empty((n_boot, pnl.shape[1]))
    for b in range(n_boot):
        draws[b] = (pnl[idx[b]].mean(0) - mu) / (sd / math.sqrt(n))      # centred on the null
    p_boot = maxt_pvalues(t, null_draws=draws)
    p_gauss = maxt_pvalues(t, np.corrcoef(pnl.T), n_sim=200_000, seed=1)
    i = int(np.argmax(t))
    return {"t_best": float(t[i]), "p_boot": float(p_boot[i]), "p_gauss": float(p_gauss[i]), "block": b_sb,
            "max_draws": draws.max(axis=1), "crit_boot": float(np.quantile(draws.max(axis=1), 0.95))}
