"""The research process in numbers (One Quant Book 7, chapter 1).

How likely is a significant backtest to be a true strategy (the positive predictive value, after
Ioannidis 2005), how often the best of many worthless variants looks excellent, how a logged trial
count deflates a Sharpe ratio, and how much evidence a live track record carries against its
backtest. Null annual Sharpe ratios estimated from Y years of daily returns are taken as
N(0, 1/Y), the large-sample law (Book 4, chapter 11). NumPy only.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
sys.path.insert(0, str(ROOT / "multitest"))
sys.path.insert(0, str(ROOT / "researchlog"))
from firm_multitest import deflated_sharpe, expected_max_sr, norm_cdf, norm_ppf  # noqa: E402
from firm_researchlog import ResearchLog  # noqa: E402

DAYS = 252


def ppv(prior: float, power: float, alpha: float, stages: int = 1) -> float:
    """Probability that a strategy is real given that it passed `stages` independent tests, each
    with the given power and size, when a fraction `prior` of the ideas tested are real."""
    t = prior * power**stages
    return t / (t + (1.0 - prior) * alpha**stages)


def p_single(threshold: float, years: float) -> float:
    """P(a worthless strategy's estimated annual Sharpe ratio >= threshold)."""
    return 1.0 - float(norm_cdf(threshold * math.sqrt(years)))


_X, _W = np.polynomial.hermite_e.hermegauss(96)
_W = _W / math.sqrt(2.0 * math.pi)


def p_best(threshold: float, n: int, years: float, rho: float = 0.0) -> float:
    """P(the best of n worthless variants reaches the threshold), the variants' estimates being
    equicorrelated with correlation rho: Z_i = sqrt(rho) W + sqrt(1 - rho) e_i, averaged over W."""
    c = threshold * math.sqrt(years)
    if rho <= 0.0:
        return 1.0 - float(norm_cdf(c)) ** n
    z = (c - math.sqrt(rho) * _X) / math.sqrt(1.0 - rho)
    return float(np.sum(_W * (1.0 - np.asarray(norm_cdf(z)) ** n)))


def expected_best(n: int, years: float) -> float:
    """Expected annual Sharpe ratio of the best of n independent worthless variants."""
    return expected_max_sr(n, 1.0 / years)


def deflated_annual(sr_annual: float, years: float, n_trials: int) -> float:
    """Deflated Sharpe ratio of an annual Sharpe ratio estimated from `years` of daily returns, the best
    of n_trials (normal returns; null variance 1/n per period)."""
    n_obs = int(round(years * DAYS))
    sr = sr_annual / math.sqrt(DAYS)
    sr0 = expected_max_sr(n_trials, 1.0 / n_obs) if n_trials > 1 else 0.0
    return deflated_sharpe(sr, n_obs, 0.0, 3.0, sr0)


def kill_pvalue(claimed: float, live: float, years: float) -> float:
    """One-sided p-value of a live annual Sharpe ratio this low if the claimed one were true."""
    return float(norm_cdf((live - claimed) * math.sqrt(years)))


def years_to_detect(sr: float, alpha: float = 0.05, power: float = 0.8) -> float:
    """Years of live returns for a one-sided test of size alpha to tell sr from zero with this power."""
    return ((float(norm_ppf(1.0 - alpha)) + float(norm_ppf(power))) / sr) ** 2


def friday(threshold=2.0, per_week=20, weeks=50, years=2.0, rho=0.6):
    """The weekend problem: a year of weekly searches of correlated worthless variants."""
    week = p_best(threshold, per_week, years, rho)
    return {
        "p_single": p_single(threshold, years),
        "p_week_indep": p_best(threshold, per_week, years),
        "p_week_corr": week,
        "p_year_corr": 1.0 - (1.0 - week) ** weeks,
        "p_year_indep": p_best(threshold, per_week * weeks, years),
        "expected_best_indep": expected_best(per_week * weeks, years),
        "dsr_1": deflated_annual(threshold, years, 1),
        "dsr_20": deflated_annual(threshold, years, per_week),
        "dsr_1000": deflated_annual(threshold, years, per_week * weeks),
    }


SEED = 1
LOOKBACKS = tuple(range(1, 51))


def search(seed: int = SEED, years: float = 2.0, log: ResearchLog | None = None):
    """The tutorial: fifty reversal rules (hold minus the sign of the trailing L-day return) on a
    driftless random walk with 1% daily volatility; every trial goes into the research log."""
    n = int(round(years * DAYS))
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0, 0.01, n + max(LOOKBACKS))
    log = log or ResearchLog()
    log.register("reversal", "short-horizon returns revert: liquidity providers are paid to absorb flow",
                 "2026-09-24T09:00")
    cs = np.concatenate([[0.0], np.cumsum(r)])
    srs = []
    for k, lb in enumerate(LOOKBACKS):
        t = np.arange(max(LOOKBACKS), len(r))
        pos = -np.sign(cs[t] - cs[t - lb])          # uses returns up to t - 1 only
        pnl = pos * r[t]
        sr = float(pnl.mean() / pnl.std(ddof=1) * math.sqrt(DAYS))
        srs.append(sr)
        log.trial("reversal", {"lookback": lb}, {"sr": round(sr, 6)}, f"2026-09-24T10:{k:02d}",
                  code_hash="rs_process.search", data_id=f"rw-seed{seed}")
    srs = np.array(srs)
    best = int(np.argmax(srs))
    return {"srs": srs, "best_lookback": LOOKBACKS[best], "best_sr": float(srs[best]), "log": log, "n_obs": n}
