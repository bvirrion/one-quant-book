"""Half-life, decay and stability (One Quant Book 7, chapter 13).

On firm.synthmkt (seed 1): IC decay curves of four predictors (one-day reversal, 12-1 momentum, the latest earnings
surprise held for 60 days, book-to-price as known), their curve half-lives and signal half-lives, and the stability
of monthly ICs across years with the CUSUM and sup-F tests. On real data: the size, value and momentum factors of the
Kenneth French library before and after the papers that published them (derived statistics only, written by
rs_fetch_factors.py). The power analysis of a measured halving of an IC. NumPy and pandas only.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("decay", "synthmkt", "features"):
    sys.path.insert(0, str(ROOT / c))
from firm_decay import (  # noqa: E402
    block_bootstrap,
    cusum,
    decline_power,
    half_life_ar,
    half_life_fit,
    ic_decay,
    rank_autocorr,
    sup_f,
    sup_f_pvalue,
)
from firm_features import past_return  # noqa: E402
from firm_synthmkt import MarketConfig, simulate  # noqa: E402

DATA = pathlib.Path(__file__).resolve().parents[4] / "data" / "research"
YEAR, MONTH, HOLD = 252, 21, 60
HORIZONS = (1, 2, 3, 5, 10, 15, 20, 30, 40, 50, 60)
DEFAULT = MarketConfig()
BROKEN = MarketConfig(pead_break=6 * YEAR, pead_after=0.0)    # the drift is arbitraged away from year 7 on
CUT = MarketConfig(pead_break=6 * YEAR, pead_after=0.3)       # ... or loses 70% of its size


@functools.lru_cache(maxsize=3)
def panel(cfg: MarketConfig = DEFAULT):
    return simulate(cfg)


@functools.lru_cache(maxsize=3)
def signals(cfg: MarketConfig = DEFAULT):
    """(T, M) panels known at each close: reversal (minus today's return), momentum (12-1 month return), the latest
    earnings surprise for 60 days after its announcement, and book-to-price with the latest filed book."""
    P = panel(cfg)
    T, M = P.ret.shape
    rev = -P.ret
    mom = past_return(P.ret, YEAR - MONTH, MONTH)
    sue = np.full((T, M), np.nan)
    for t, p, s in P.earnings:
        sue[t:min(T, t + HOLD), p] = s
    book = np.full((T, M), np.nan)
    for f in sorted((x for x in P.fundamentals if x["field"] == "book"), key=lambda x: x["filed"]):
        if f["filed"] < T:
            book[f["filed"]:, f["pid"]] = f["value"]
    bp = np.where(P.listed, book / P.price, np.nan)
    return {"reversal": rev, "momentum": mom, "surprise": sue, "book-to-price": bp}


def decay_table(step: int = 3):
    P = panel()
    dates = range(2 * YEAR, P.ret.shape[0] - max(HORIZONS) - 1, step)
    out = {}
    for name, s in signals().items():
        ic = ic_decay(s, P.ret, HORIZONS, dates)
        ic0, hl = half_life_fit(HORIZONS, list(ic.values()))
        z = np.where(P.listed & np.isnan(s), 0.0, s) if name == "surprise" else s     # no news: a neutral zero
        rho = rank_autocorr(z, range(2 * YEAR, P.ret.shape[0], step))
        out[name] = {"ic": ic, "ic0": ic0, "curve_half_life": hl, "rho": rho, "signal_half_life": half_life_ar(rho)}
    return out


def monthly_ic(name: str, horizon: int = MONTH, cfg: MarketConfig = DEFAULT):
    """The IC of the signal at each month-end with the next `horizon` days' return."""
    P = panel(cfg)
    s = signals(cfg)[name]
    fwd = np.full(P.ret.shape, np.nan)
    c = np.nancumsum(np.nan_to_num(P.ret), axis=0)
    fwd[:-horizon] = c[horizon:] - c[:-horizon]
    fwd[~P.listed] = np.nan
    ends = np.arange(2 * YEAR, P.ret.shape[0] - horizon, MONTH)
    from firm_decay import _rank_corr
    return np.array([_rank_corr(s[t], fwd[t]) for t in ends])


def stability(name: str = "momentum", cfg: MarketConfig = DEFAULT):
    x = monthly_ic(name, cfg=cfg)
    W, b = cusum(x)
    f, k = sup_f(x)
    first = np.flatnonzero(np.abs(W) > b)
    years = np.array_split(x, len(x) // 12)
    boot = block_bootstrap(x, np.mean, 12, 2000, seed=2)
    return {"n": len(x), "mean": float(x.mean()), "sd": float(x.std(ddof=1)),
            "yearly": [float(y.mean()) for y in years],
            "cusum_max": float(np.max(np.abs(W) / b)), "cusum_first": int(first[0]) + 1 if len(first) else -1,
            "supf": f, "supf_at": k, "supf_p": sup_f_pvalue(x, reps=2000, seed=1),
            "ci": (float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975)))}


def detection(after: float, seeds=range(1, 11)):
    """Over markets with different seeds, the drift multiplied by `after` from year 7: the share of markets in which
    sup-F (permutation p < 0.05) and the CUSUM (crossing) detect a break in the surprise's monthly IC."""
    sf, cu = [], []
    for seed in seeds:
        cfg = MarketConfig(seed=seed, pead_break=6 * YEAR, pead_after=after)
        x = monthly_ic("surprise", cfg=cfg)
        W, b = cusum(x)
        sf.append(sup_f_pvalue(x, reps=500, seed=1) < 0.05)
        cu.append(bool(np.any(np.abs(W) > b)))
    return float(np.mean(sf)), float(np.mean(cu))


def factors():
    return pd.read_csv(DATA / "ff_decay.csv")


def posterior_curve(ts=(0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0), n: int = 60, prior: float = 0.5):
    """The posterior probability of true decay after a measured halving, against the five-year t statistic of the
    IC (mean / (sd / sqrt(n))); it depends on nothing else."""
    return {t: power(t / np.sqrt(n), 1.0, n, prior)["posterior"] for t in ts}


def power(ic: float, sd: float, n: int = 60, prior: float = 0.5):
    p = decline_power(ic, sd, n, 0.5, reps=200_000, seed=3)
    post = prior * p["decay"] / (prior * p["decay"] + (1 - prior) * p["luck"])
    return {**p, "posterior": post}
