"""Book 4, chapter 12: testing and multiple testing (teaching module).

Two hundred momentum variants on a random walk: every variant is worthless by construction, the best
looks significant, and the corrections of firm.multitest say how surprising it really is.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "multitest"))
from firm_multitest import (  # noqa: E402
    benjamini_hochberg,
    bonferroni,
    deflated_sharpe,
    effective_trials,
    expected_max_sr,
    holm,
    maxt_pvalues,
    norm_cdf,
    norm_ppf,
)

N_DAYS = 2520                    # ten years of daily returns
LOOKBACKS = np.arange(5, 205)    # 200 variants: sign of the trailing L-day return
SD = 0.01                        # daily volatility of the asset (no drift, no momentum)


def variants(seed: int = 1, n: int = N_DAYS, lookbacks=LOOKBACKS, sd: float = SD, df: float | None = None):
    """Daily P&L (rows: days, columns: variants) of trend rules on a driftless random walk."""
    rng = np.random.default_rng(seed)
    warm = int(max(lookbacks))
    r = sd * (rng.standard_normal(n + warm) if df is None else rng.standard_t(df, n + warm) / math.sqrt(df / (df - 2)))
    c = np.concatenate([[0.0], np.cumsum(r)])
    pnl = np.empty((n, len(lookbacks)))
    for j, L in enumerate(lookbacks):
        sig = np.sign(c[warm:warm + n] - c[warm - L:warm + n - L])
        pnl[:, j] = sig * r[warm:]
    return pnl


def tstats(pnl: np.ndarray) -> np.ndarray:
    return pnl.mean(0) / (pnl.std(0, ddof=1) / math.sqrt(pnl.shape[0]))


SEED = 336                       # the 336th history tried gave a best t near 3.1 (see the chapter)


# --- Section 1: size, power, and the sample size a Sharpe ratio needs ----------------------------

def sharpe_power(sr_annual: float, years: float, alpha: float = 0.05) -> float:
    """Power of the one-sided test of SR = 0 at level alpha after `years` of iid returns."""
    return float(norm_cdf(sr_annual * math.sqrt(years) - norm_ppf(1 - alpha)))


def years_needed(sr_annual: float, alpha: float = 0.05, power: float = 0.8) -> float:
    return ((norm_ppf(1 - alpha) + norm_ppf(power)) / sr_annual) ** 2


def kolmogorov_sf(lam: float, terms: int = 100) -> float:
    """P(sqrt(n) D_n > lam) in the limit: 2 sum (-1)^(k-1) exp(-2 k^2 lam^2)."""
    if lam <= 0:
        return 1.0
    return float(min(1.0, 2 * sum((-1) ** (k - 1) * math.exp(-2 * k * k * lam * lam) for k in range(1, terms + 1))))


def ks_test(x, cdf) -> tuple[float, float]:
    """Kolmogorov-Smirnov statistic D_n = sup |F_n - F| against a fully specified cdf, and its p-value."""
    x = np.sort(np.asarray(x, dtype=float))
    n = x.size
    f = cdf(x)
    d = float(max(np.max(np.arange(1, n + 1) / n - f), np.max(f - np.arange(n) / n)))
    return d, kolmogorov_sf(math.sqrt(n) * d)


def ks_example(n: int = 1000, seed: int = 12, df: float = 4.0) -> dict:
    """Daily returns from a Student t (df 4) scaled to 1% volatility, tested against N(0, 1%^2)."""
    rng = np.random.default_rng(seed)
    x = SD * rng.standard_t(df, n) / math.sqrt(df / (df - 2))
    d, p = ks_test(x, lambda u: norm_cdf(u / SD))
    lam95 = _bisect(lambda lam: kolmogorov_sf(lam) - 0.05, 0.5, 3.0)
    return {"d": d, "p": p, "crit95": lam95 / math.sqrt(n), "lam95": lam95}


def _bisect(f, lo: float, hi: float) -> float:
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


# --- Section 2: the maximum of many t-statistics --------------------------------------------------

def max_survival(c, n_trials: int) -> np.ndarray:
    """P(max of n independent N(0,1) >= c)."""
    return 1 - norm_cdf(c) ** n_trials


def correlated_max_draws(seed: int = SEED, n_sim: int = 200_000, sim_seed: int = 1) -> np.ndarray:
    from firm_multitest import _gaussian_null
    return _gaussian_null(np.corrcoef(variants(seed).T), n_sim, sim_seed).max(axis=1)


def family_exceedance(threshold: float, n_hist: int = 2000, seed0: int = 10_000, df: float | None = None) -> float:
    """Share of fresh histories in which the best of the 200 variants has t >= threshold."""
    return float(np.mean([tstats(variants(seed0 + k, df=df)).max() >= threshold for k in range(n_hist)]))


# --- Section 3: family-wise error and false discoveries -------------------------------------------

def fdr_experiment(m: int = 1000, m1: int = 100, shift: float = 3.0, n_rep: int = 500, alpha: float = 0.05,
                   seed: int = 5) -> dict:
    """m one-sided tests, m1 of them real with t ~ N(shift, 1); average outcomes of four rules."""
    rng = np.random.default_rng(seed)
    rules = {"none": lambda p: p, "bonferroni": bonferroni, "holm": holm, "bh": benjamini_hochberg}
    acc = {k: {"disc": 0.0, "false": 0.0, "fdp": 0.0, "any_false": 0} for k in rules}
    for _ in range(n_rep):
        z = rng.standard_normal(m)
        z[:m1] += shift
        p = 1 - norm_cdf(z)
        for k, rule in rules.items():
            rej = rule(p) <= alpha
            d, f = int(rej.sum()), int(rej[m1:].sum())
            acc[k]["disc"] += d / n_rep
            acc[k]["false"] += f / n_rep
            acc[k]["fdp"] += (f / d if d else 0.0) / n_rep
            acc[k]["any_false"] += int(f > 0)
    for k in acc:
        acc[k]["fwer"] = acc[k].pop("any_false") / n_rep
        acc[k]["true"] = acc[k]["disc"] - acc[k]["false"]
    return acc


# --- Section 4 and the problem ---------------------------------------------------------------------

def problem(seed: int = SEED, n_sim: int = 200_000) -> dict:
    pnl = variants(seed)
    t = tstats(pnl)
    i = int(np.argmax(t))
    p = 1 - norm_cdf(t)
    corr = np.corrcoef(pnl.T)
    p_max = maxt_pvalues(t, corr, n_sim=n_sim, seed=1)
    p_step = maxt_pvalues(t, corr, n_sim=n_sim, seed=1, stepdown=True)
    x = pnl[:, i]
    sr = x.mean() / x.std(ddof=1)
    z = (x - x.mean()) / x.std()
    skew, kurt = float(np.mean(z**3)), float(np.mean(z**4))
    n_eff = effective_trials(float(p[i]), float(p_max[i]))
    v_null = 1.0 / N_DAYS
    from firm_multitest import _gaussian_null
    mx = _gaussian_null(corr, n_sim, 1).max(axis=1)
    return {
        "best_lookback": int(LOOKBACKS[i]), "t_best": float(t[i]), "sr_best": sr * math.sqrt(252),
        "p_naive": float(p[i]), "p_bonf": float(bonferroni(p)[i]), "p_holm": float(holm(p)[i]),
        "p_bh": float(benjamini_hochberg(p)[i]), "p_maxt": float(p_max[i]), "p_step": float(p_step[i]),
        "p_indep": float(max_survival(t[i], t.size)), "n_eff": n_eff,
        "n_naive_5": int(np.sum(p <= 0.05)), "n_bh_5": int(np.sum(benjamini_hochberg(p) <= 0.05)),
        "n_bonf_5": int(np.sum(bonferroni(p) <= 0.05)), "n_maxt_5": int(np.sum(p_max <= 0.05)),
        "crit_maxt": float(np.quantile(mx, 0.95)), "crit_bonf": float(norm_ppf(1 - 0.05 / t.size)),
        "mean_max": float(mx.mean()), "mean_t": float(t.mean()),
        "corr_next": float(corr[i, i + 1]), "corr_first": float(corr[i, 0]), "corr_last": float(corr[i, -1]),
        "skew": skew, "kurt": kurt,
        "sr0_200": expected_max_sr(t.size, v_null) * math.sqrt(252),
        "sr0_eff": expected_max_sr(n_eff, v_null) * math.sqrt(252),
        "dsr_200": deflated_sharpe(sr, N_DAYS, skew, kurt, expected_max_sr(t.size, v_null)),
        "dsr_eff": deflated_sharpe(sr, N_DAYS, skew, kurt, expected_max_sr(n_eff, v_null)),
        "psr": deflated_sharpe(sr, N_DAYS, skew, kurt, 0.0),
    }


def fdr_correlated(rho: float = 0.5, m: int = 1000, m1: int = 100, shift: float = 3.0, n_rep: int = 500,
                   q: float = 0.05, seed: int = 7) -> dict:
    """Exercise 7: Benjamini-Hochberg with equicorrelated test statistics (one common factor)."""
    rng = np.random.default_rng(seed)
    fdp, disc = [], []
    for _ in range(n_rep):
        z = math.sqrt(rho) * rng.standard_normal() + math.sqrt(1 - rho) * rng.standard_normal(m)
        z[:m1] += shift
        rej = benjamini_hochberg(1 - norm_cdf(z)) <= q
        d = int(rej.sum())
        fdp.append(int(rej[m1:].sum()) / max(d, 1))
        disc.append(d)
    fdp_a = np.array(fdp)
    return {"fdr": float(fdp_a.mean()), "p_fdp_over_10": float(np.mean(fdp_a > 0.1)), "disc": float(np.mean(disc))}
