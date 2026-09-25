"""Systematic macro (One Quant Book 9, chapter 16).

Synthetic: firm.sysmacro on firm.synthfut's ten equity indices, ten government bonds and ten currencies over thirty
years, with a planted valuation gap per market (sd 10%, half-life three years) seen through a fair-value anchor with
a persistent 10% error, and a planted economic-surprise index per country (half-life 60 days) seen with noise. Five
signals traded long-short within each class monthly and scaled to 10% volatility: value (the anchor), value from
prices (the five-year reversal), momentum, carry and surprise; their correlations and equal-risk combinations. NumPy.
"""
from __future__ import annotations

import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
for p in ("synthfut", "sysmacro"):
    sys.path.insert(0, str(ROOT / "firm" / p))
from firm_sysmacro import YEAR, MacroConfig, combine, macro_market, portfolio  # noqa: E402

SIGNALS = ("value", "reversal", "momentum", "carry", "surprise")
START = 5 * YEAR + 2 * 64               # five years for the reversal signal, two quarters for the vol scalings


@functools.lru_cache(maxsize=1)
def books():
    cfg = MacroConfig()
    m = macro_market(cfg)
    b = {n: portfolio(m, n, cfg) for n in SIGNALS}
    b["combined"] = combine([b[k] for k in ("value", "momentum", "carry", "surprise")], cfg)
    b["combined, price value"] = combine([b[k] for k in ("reversal", "momentum", "carry", "surprise")], cfg)
    b["combined, no value"] = combine([b[k] for k in ("momentum", "carry", "surprise")], cfg)
    return cfg, m, b


def stats():
    _, _, b = books()
    out = {}
    for k, x in b.items():
        x = x[START:]
        cum = np.cumsum(x)
        d = x - x.mean()
        out[k] = {"sr": float(x.mean() / x.std() * math.sqrt(YEAR)), "vol": float(x.std() * math.sqrt(YEAR)),
                  "skew": float((d**3).mean() / (d**2).mean() ** 1.5),
                  "max_dd": float((cum - np.maximum.accumulate(cum)).min())}
    return out


def correlations():
    _, _, b = books()
    return np.corrcoef(np.vstack([b[k][START:] for k in SIGNALS]))


def years():
    return (len(books()[2]["value"]) - START) / YEAR


def noisy_anchor(noise: float = 0.3):
    """Exercise 7: value and the four-signal combination when the anchor's error is `noise`."""
    cfg = MacroConfig(anchor_noise=noise)
    m = macro_market(cfg)
    b = {n: portfolio(m, n, cfg) for n in ("value", "momentum", "carry", "surprise")}
    c = combine(list(b.values()), cfg)
    sr = lambda x: float(x[START:].mean() / x[START:].std() * math.sqrt(YEAR))    # noqa: E731
    return {"value": sr(b["value"]), "combined": sr(c)}
