"""Skew and term-structure relative value (One Quant Book 9, chapter 3).

Synthetic: firm.synthvol's index (twenty years, three crashes) with firm.volrv's daily surface: fair one- and
three-month vols from the variance dynamics, a fair skew that steepens as the level rises, and two planted noises
(skew and three-month vol, AR(1), half-life 34 days). Signals are expanding z-scores (clipped at 2) of the raw skew
and slope, or of their residuals on the level; each month the book holds minus the signal in a vega-neutral,
delta-hedged risk reversal or calendar, attributed to spot and time, level, skew and slope. Real: Cboe's VIX term
structure (VIX3M minus VIX), SKEW index and cross-index vol spreads, as derived statistics. NumPy.
"""
from __future__ import annotations

import csv
import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
for p in ("synthvol", "volrv"):
    sys.path.insert(0, str(ROOT / "firm" / p))
from firm_synthvol import VolConfig, simulate_vol  # noqa: E402
from firm_volrv import SurfaceConfig, attribution, features, surface_path, trade_pnl  # noqa: E402

DATA = ROOT.parent / "data" / "strategies-2"
WARMUP = 12                    # months dropped while the regressions and z-scores warm up
BOOKS = (("skew raw", "skew", "skew"), ("skew residual", "skew", "skew_res"),
         ("calendar raw", "calendar", "slope"), ("calendar residual", "calendar", "slope_res"))


def zscore(x, warmup: int = 252, cap: float = 2.0):
    """Expanding z-score using data up to each day only, clipped at +-cap; zero during the warm-up."""
    x = np.asarray(x, float)
    n = np.arange(1, len(x) + 1)
    m = np.cumsum(x) / n
    sd = np.sqrt(np.maximum(np.cumsum(x * x) / n - m * m, 1e-18))
    out = np.zeros(len(x))
    out[warmup:] = ((x - m) / sd)[warmup:]
    return np.clip(out, -cap, cap)


@functools.lru_cache(maxsize=16)
def market(seed: int = 0, noise: float = 1.0):
    """The synthetic index and surface; noise scales both planted noises (0 switches them off)."""
    cfg, base = VolConfig(seed=91 + seed), SurfaceConfig(seed=93 + seed)
    sim = simulate_vol(cfg)
    scfg = SurfaceConfig(seed=93 + seed, skew_sd=noise * base.skew_sd, slope_sd=noise * base.slope_sd)
    s = surface_path(sim["r"], sim["v"], cfg, scfg)
    return cfg, sim, s, features(s)


@functools.lru_cache(maxsize=16)
def books(seed: int = 0, noise: float = 1.0):
    """Each book's monthly P&L buckets: sell what is rich, so hold minus the z-scored feature."""
    cfg, sim, s, f = market(seed, noise)
    out = {}
    for name, kind, feat in BOOKS:
        b = trade_pnl(sim["r"], s, kind, -zscore(f[feat]), cfg)
        out[name] = {k: v[WARMUP:] for k, v in b.items()}
    return out


def stats(x):
    x = np.asarray(x, float)
    d = x - x.mean()
    return {"sr": float(x.mean() / x.std(ddof=1) * math.sqrt(12)),
            "skewness": float((d**3).mean() / (d**2).mean() ** 1.5), "worst_sd": float(x.min() / x.std(ddof=1)),
            "share_up": float((x > 0).mean())}


def table(seed: int = 0, noise: float = 1.0):
    return {name: {**stats(b["total"]), **attribution(b)} for name, b in books(seed, noise).items()}


def bucket_sr(seed: int = 0):
    return {name: {k: stats(b[k])["sr"] for k in ("spot_time", "level", "skew", "slope") if np.std(b[k]) > 0}
            for name, b in books(seed).items()}


def seeds(n: int = 8):
    """Each book's Sharpe ratio over n seeds of the market and the surface."""
    return {name: [table(k)[name]["sr"] for k in range(n)] for name, _, _ in BOOKS}


def fit():
    """How well the residuals recover the planted noises, and the fitted level betas."""
    _, _, s, f = market(0)
    lv = f["level"]
    return {"corr_skew": float(np.corrcoef(f["skew_res"][252:], s["e_skew"][252:])[0, 1]),
            "corr_slope": float(np.corrcoef(f["slope_res"][252:], s["e_slope"][252:])[0, 1]),
            "beta_skew": float(np.polyfit(lv, f["skew"], 1)[0]), "beta_slope": float(np.polyfit(lv, f["slope"], 1)[0]),
            "corr_raw_skew_level": float(np.corrcoef(f["skew"], lv)[0, 1]),
            "corr_raw_slope_level": float(np.corrcoef(f["slope"], lv)[0, 1])}


def real():
    with open(DATA / "term_summary.csv") as fh:
        out = {}
        for r in csv.DictReader(fh):
            out.setdefault(r["series"], {})[r["stat"]] = r["value"]
        return out


def static(seed: int = 0):
    """Mean monthly buckets of one unit held every month (long the call wing, short the put; or long the calendar)."""
    cfg, sim, s, _ = market(seed)
    out = {}
    for kind in ("skew", "calendar"):
        b = trade_pnl(sim["r"], s, kind, np.ones(len(sim["r"])), cfg)
        out[kind] = {k: float(b[k][WARMUP:].mean()) for k in ("spot_time", "level", "skew", "slope", "total")}
    return out


def carry_link(seed: int = 0):
    """Correlation, across months, of the spot-and-time bucket with the mispricing held (minus position x noise)."""
    _, _, s, f = market(seed)
    out = {}
    for name, feat, noise in (("skew residual", "skew_res", "e_skew"), ("calendar residual", "slope_res", "e_slope")):
        b = books(seed)[name]
        held = zscore(f[feat])[b["start"]] * s[noise][b["start"]]
        out[name] = float(np.corrcoef(b["spot_time"], held)[0, 1])
    return out


def worst(name: str = "skew residual", seed: int = 0):
    """The book's worst month: start day, position, index return over the month, one-month vol at start and end."""
    _, sim, s, f = market(seed)
    feat = dict((n, ft) for n, _, ft in BOOKS)[name]
    b = books(seed)[name]
    i = int(np.argmin(b["total"]))
    t0 = int(b["start"][i])
    return {"start": t0, "pos": float(-zscore(f[feat])[t0]), "ret": float(np.expm1(sim["r"][t0 + 1:t0 + 22].sum())),
            "atm_start": float(s["atm1"][t0]), "atm_end": float(s["atm1"][t0 + 21]),
            **{k: float(b[k][i]) for k in ("spot_time", "level", "skew", "total")}}
