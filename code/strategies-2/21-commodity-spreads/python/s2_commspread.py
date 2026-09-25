"""Commodity spreads (One Quant Book 9, chapter 21).

Synthetic: firm.commspread's ten-year market (crude, a seasonal and mean-reverting crack that lags crude, a location
spread with a planted pipeline bottleneck in year 6, a quality spread); fading each spread, the crack with and without
its season removed, a February-to-April seasonal crack, and their equal-risk combination; the location fade through
the bottleneck. Real: statistics of EIA spot crack and Brent-WTI spreads (s2_fetch_spreads.py). NumPy.
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
DATA = ROOT.parent / "data" / "strategies-2"
sys.path.insert(0, str(ROOT / "firm" / "commspread"))
from firm_commspread import YEAR, SpreadConfig, fade, seasonal, simulate_spreads  # noqa: E402

RULES = ("crack", "crack_deseason", "seasonal", "location", "quality")


@functools.lru_cache(maxsize=1)
def market():
    cfg = SpreadConfig()
    s = simulate_spreads(cfg)
    books = {"crack": fade(s["crack"], cfg)[0], "crack_deseason": fade(s["crack"], cfg, s["month"])[0],
             "seasonal": seasonal(s["crack"], s["month"], cfg), "location": fade(s["location"], cfg)[0],
             "quality": fade(s["quality"], cfg)[0]}
    live = {k: v[YEAR:] for k, v in books.items()}
    parts = [live[k] / live[k].std() for k in ("crack", "seasonal", "location", "quality")]
    books["combined"] = np.concatenate([np.zeros(YEAR), np.mean(parts, axis=0)])
    return cfg, s, books


def table() -> dict:
    """Annual P&L ($/bbl per unit), Sharpe ratio and correlation with crude's daily change, after the first year."""
    _, s, books = market()
    dc = np.diff(s["crude"], prepend=s["crude"][0])[YEAR:]
    out = {}
    for k, b in books.items():
        x = b[YEAR:]
        out[k] = {"annual": float(x.mean() * YEAR), "sr": float(x.mean() / x.std() * math.sqrt(YEAR)),
                  "corr": float(np.corrcoef(x, dc)[0, 1])}
    return out | {"spread_corr": float(np.corrcoef(np.diff(s["crack"]), np.diff(s["crude"]))[0, 1])}


def bottleneck() -> dict:
    """The location fade before and through the planted bottleneck ($/bbl per unit)."""
    cfg, s, books = market()
    a, p = cfg.shock_start, books["location"]
    return {"before": float(p[YEAR:a].sum()), "first_half": float(p[a:a + cfg.shock_days // 2].sum()),
            "through": float(p[a:a + cfg.shock_days + 42].sum()), "after": float(p[a + cfg.shock_days + 42:].sum())}


def real() -> dict:
    with open(DATA / "spreads_summary.csv") as fh:
        rows = {r["key"]: r["value"] for r in csv.DictReader(fh)}
    return {k: (v if ("date" in k or k in ("first", "last")) else float(v)) for k, v in rows.items()}


def bands(values=(1.0, 1.5, 2.0)) -> dict:
    """The crack fade's Sharpe ratio and share of days in the market for several entry bands."""
    _, s, _ = market()
    out = {}
    for b in values:
        cfg = SpreadConfig(band=b)
        p, pos = fade(s["crack"], cfg)
        x = p[YEAR:]
        out[b] = {"sr": float(x.mean() / x.std() * math.sqrt(YEAR)), "inmarket": float((pos[YEAR:] != 0).mean())}
    return out
