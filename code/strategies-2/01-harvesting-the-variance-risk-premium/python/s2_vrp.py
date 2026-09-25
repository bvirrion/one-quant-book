"""Harvesting the variance risk premium (One Quant Book 9, chapter 1).

Synthetic: firm.synthvol's twenty years of an index (stochastic variance around 16%, leverage correlation -0.7,
negative jumps, three ten-day crashes of 25%, 20% and 30%; implied variance 30% above the expected variance, a
skewed smile) and firm.shortvol's monthly implementations: a short variance swap, a delta-hedged short
at-the-money straddle, covered-call overwriting 2% out of the money, put writing 5% out of the money, and a short
variance swap sized by the inverse of its variance strike. Each is scaled to a target annual volatility and levered
through the crashes. Real: Cboe's VIX against the next month's realised S&P 500 volatility (1990-2026) and the Cboe
PutWrite and BuyWrite indices against the S&P 500 (2007-2026), as derived statistics in data/strategies-2.
NumPy and pandas.
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
for p in ("synthvol", "shortvol"):
    sys.path.insert(0, str(ROOT / "firm" / p))
from firm_shortvol import hedged_straddle, lever, overwrite, periods, put_write, short_variance  # noqa: E402
from firm_synthvol import VolConfig, atm_iv, simulate_vol  # noqa: E402

DATA = ROOT.parent / "data" / "strategies-2"
TENOR = 21


@functools.lru_cache(maxsize=1)
def market():
    cfg = VolConfig()
    return cfg, simulate_vol(cfg)


@functools.lru_cache(maxsize=1)
def implementations():
    cfg, S = market()
    r, v = S["r"], S["v"]
    starts = periods(len(r), TENOR)
    strike = atm_iv(v[starts], cfg, TENOR / 252) ** 2
    var = short_variance(r, v, cfg, TENOR)
    out = {"short variance": var, "hedged straddle": hedged_straddle(r, v, cfg, TENOR),
           "overwrite": overwrite(r, v, cfg, TENOR), "put write": put_write(r, v, cfg, TENOR),
           "variance, 1/strike": var / strike * strike.mean(),
           "index": np.array([math.expm1(r[s + 1:s + 1 + TENOR].sum()) for s in starts])}
    return out, starts


def stats(x):
    x = np.asarray(x, float)
    d = x - x.mean()
    return {"sr": float(x.mean() / x.std(ddof=1) * math.sqrt(12)), "skew": float((d**3).mean() / (d**2).mean() ** 1.5),
            "worst_sd": float(x.min() / x.std(ddof=1)), "share_up": float((x > 0).mean()), "worst_at": int(x.argmin())}


def leverage_table(vols=(0.05, 0.10, 0.20, 0.40, 0.60)):
    """Short variance scaled to each annual volatility: Sharpe ratio before its worst month, the worst month's loss,
    and whether the capital was wiped out."""
    x = implementations()[0]["short variance"]
    unit = x / (x.std(ddof=1) * math.sqrt(12))
    w = int(x.argmin())
    out = {}
    for vol in vols:
        y = unit * vol
        before = y[:w]
        cap, dead = lever(y, 1.0)
        out[vol] = {"sr_before": float(before.mean() / before.std(ddof=1) * math.sqrt(12)),
                    "worst": float(y[w]), "dead": dead, "final": float(cap[-1])}
    return out


def paths(vols=(0.10, 0.20, 0.40)):
    x = implementations()[0]["short variance"]
    unit = x / (x.std(ddof=1) * math.sqrt(12))
    return {vol: lever(unit * vol, 1.0)[0] for vol in vols}


def real():
    rd = lambda n: list(csv.DictReader(open(DATA / n)))  # noqa: E731
    return rd("vrp_summary.csv")[0], rd("vrp_worst.csv"), {w["index"]: w for w in rd("writers.csv")}
