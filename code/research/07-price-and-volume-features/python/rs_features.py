"""Price and volume features (One Quant Book 7, chapter 7).

The bar-feature family measured on firm.synthmkt at three horizons (one day, one week, one month), with
non-overlapping sampling so that the naive t-statistics are valid; the information coefficient of a feature against
the horizon of its target; the weights a moving-average crossover puts on past returns; and a race between the range
estimators of daily variance on simulated intraday paths, with drift and with opening gaps. NumPy only.
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("synthmkt", "predictor", "features"):
    sys.path.insert(0, str(ROOT / c))
from firm_features import (  # noqa: E402
    amihud,
    garman_klass,
    ma_crossover,
    parkinson,
    past_return,
    rogers_satchell,
    rolling_vol,
    turnover,
    volume_surprise,
    yang_zhang,
)
from firm_predictor import forward_return, ic_series, ic_summary  # noqa: E402
from firm_synthmkt import MarketConfig, simulate  # noqa: E402

BURN = 260
HORIZONS = (1, 5, 21)


@functools.lru_cache(maxsize=1)
def panel():
    return simulate(MarketConfig())


@functools.lru_cache(maxsize=1)
def features() -> dict:
    p = panel()
    ret = np.where(p.listed, p.ret, np.nan)
    price = np.where(p.listed, p.price, np.nan)
    vol = np.where(p.listed, p.volume, np.nan)
    sh = np.where(p.listed, p.shares, np.nan)
    return {
        "reversal 1d": -past_return(ret, 1), "reversal 5d": -past_return(ret, 5), "reversal 21d": -past_return(ret, 21),
        "momentum 12-1": past_return(ret, 231, 21), "momentum 12": past_return(ret, 252),
        "momentum 6-1": past_return(ret, 105, 21), "low volatility": -rolling_vol(ret, 21),
        "volume surprise": volume_surprise(vol, 21), "Amihud illiquidity": amihud(ret, vol * price, 21),
        "low turnover": -turnover(vol, sh, 21), "crossover 5/20": ma_crossover(price, 5, 20),
        "crossover 50/200": ma_crossover(price, 50, 200),
    }


def _ic_at(f: np.ndarray, h: int, step: int | None = None) -> dict:
    ret = np.where(panel().listed, panel().ret, np.nan)
    fwd = forward_return(ret, h)
    step = step or h
    return ic_summary(ic_series(f[BURN:-h:step], fwd[BURN:-h:step], "rank"), h=1, periods=252 // step)


@functools.lru_cache(maxsize=1)
def ic_table() -> dict:
    """{feature: {h: (mean IC, t)}} with one observation every h days."""
    return {k: {h: (s["mean"], s["t_naive"]) for h in HORIZONS for s in [_ic_at(f, h)]} for k, f in features().items()}


def ic_by_horizon(name: str, hs=(1, 2, 5, 10, 21, 42, 63)) -> dict:
    """Mean IC against h-day targets, scored every day (the means are unbiased; overlap only affects errors)."""
    f = features()[name]
    return {h: _ic_at(f, h, step=1)["mean"] for h in hs}


def lag_profile(name: str, ks=(1, 21, 63, 126, 189, 252)) -> dict:
    """Mean rank IC of a feature at the close of t against the single-day return of day t + k, over every date (a
    momentum IC series is dominated by a few days of large factor moves: a sample of every fifth date gives means from
    0.004 to 0.020 depending on its starting day)."""
    f = features()[name]
    ret = np.where(panel().listed, panel().ret, np.nan)
    return {k: ic_summary(ic_series(f[BURN:-k], ret[BURN + k:], "rank"))["mean"] for k in ks}


def half_life(profile: dict) -> float:
    """Half-life (days) of a least-squares exponential fitted to the positive values of an IC lag profile."""
    k = np.array([x for x, v in profile.items() if v > 0], float)
    v = np.array([v for v in profile.values() if v > 0], float)
    slope = np.polyfit(k, np.log(v), 1)[0]
    return float(math.log(0.5) / slope) if slope < 0 else float("inf")


def crossover_filter(short: int = 5, long: int = 20) -> np.ndarray:
    from firm_features import crossover_weights
    return crossover_weights(short, long)


def range_race(days: int = 4000, steps: int = 390, sigma: float = 0.01, drift: float = 0.0, gap_share: float = 0.0,
               seed: int = 5, window: int = 20) -> dict:
    """Daily variance estimators on simulated days: an overnight gap with variance gap_share * sigma^2, then a
    Brownian path of `steps` steps with total variance (1 - gap_share) * sigma^2 and a drift of `drift` over the day.
    For each estimator: its mean relative to the daily diffusion variance sigma^2 (bias; close-to-close squared returns
    also contain drift^2) and the variance of close-to-close squared returns divided by its own variance (efficiency).
    Yang-Zhang is scored on rolling windows against the
    close-to-close variance over the same windows."""
    rng = np.random.default_rng(seed)
    s_in = sigma * math.sqrt(1.0 - gap_share)
    inc = rng.normal(drift / steps, s_in / math.sqrt(steps), (days, steps))
    path = np.cumsum(inc, axis=1)
    gap = rng.normal(0.0, sigma * math.sqrt(gap_share), days)
    o = np.exp(np.cumsum(np.r_[0.0, (gap[1:] + path[:-1, -1])]))    # log open accumulates previous closes and gaps
    hi = o * np.exp(np.maximum(path.max(axis=1), 0.0))
    lo = o * np.exp(np.minimum(path.min(axis=1), 0.0))
    c = o * np.exp(path[:, -1])
    true = sigma**2
    cc = np.log(c[1:] / c[:-1]) ** 2
    ests = {"Parkinson": parkinson(hi, lo)[1:], "Garman-Klass": garman_klass(o, hi, lo, c)[1:],
            "Rogers-Satchell": rogers_satchell(o, hi, lo, c)[1:]}
    out = {"close-to-close": {"bias": float(cc.mean() / true), "efficiency": 1.0}}
    for k, e in ests.items():
        out[k] = {"bias": float(e.mean() / true), "efficiency": float(cc.var() / e.var())}
    yz = yang_zhang(o, hi, lo, c, window)
    ccw = np.array([np.var(np.log(c[t - window + 1: t + 1] / c[t - window: t]), ddof=1) for t in range(window, days)])
    yzw = yz[window:]
    ok = ~np.isnan(yzw)
    out["Yang-Zhang (20 days)"] = {"bias": float(np.mean(yzw[ok]) / true),
                                   "efficiency": float(ccw[ok].var() / yzw[ok].var())}
    return out
