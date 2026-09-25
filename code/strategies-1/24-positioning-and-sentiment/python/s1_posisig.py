"""Positioning and sentiment (One Quant Book 8, chapter 24).

Synthetic: firm.synthfut's ten commodities (thirty years) with planted hedging pressure (firm.posisig): hedgers'
net short position, an AR(1) with a half-life of 20 days in standard deviations, earns the speculators who absorb it
a premium of 0.3 times the market's volatility a year per standard deviation; speculators' reported net long is the
hedging pressure plus half a standard deviation per unit of their 60-day trend and noise. Positions are measured on
Tuesdays and known after a publication lag of 0, 3 (Friday), 10 or 21 days; each signal's daily rank IC with the
next five days' return is measured across the ten markets (t-statistics corrected for the five-day overlap), and
extreme speculative longs (a 52-week z-score above 1.5) are followed for a quarter. Real data: CBOT corn managed
money's net position as a share of open interest (CFTC disaggregated COT, 2016-2026), its 52-week z-score as
published by each month's end, against the IMF maize price's next monthly change (monthly averages, skipping one
month so that the signal's month does not overlap the return), 2017-2026. NumPy only.
"""
from __future__ import annotations

import calendar
import csv
import datetime as dt
import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
for p in ("synthfut", "posisig", "cot"):
    sys.path.insert(0, str(ROOT / "firm" / p))
from firm_cot import net_share  # noqa: E402
from firm_posisig import forward, hedging_market, ic, published, zscore  # noqa: E402
from firm_synthfut import simulate_futures  # noqa: E402

HALF_LIFE, PREMIUM, CHASE, NOISE = 20.0, 0.3, 0.5, 0.5
LAGS = (0, 3, 10, 21)
DATA = ROOT.parent / "data" / "markets-3"


@functools.lru_cache(maxsize=2)
def market(half_life: float = HALF_LIFE):
    F = simulate_futures()
    r = F["r"][:, F["cls"] == 3]
    vol = r.std(0) * math.sqrt(252)
    return hedging_market(r, vol, half_life, PREMIUM, CHASE, NOISE, np.random.default_rng(24))


@functools.lru_cache(maxsize=2)
def lag_table(half_life: float = HALF_LIFE):
    M = market(half_life)
    f = forward(M["r"], 5)
    out = {}
    for lag in LAGS:
        out[lag] = {k: ic(published(M[k], 5, 1, lag), f, 1, 5) for k in ("hedge", "spec")}
    return out


def extremes():
    """Mean next-63-day return (in annual volatilities) after speculators' 52-week z-score is above 1.5, below -1.5,
    or in between, from Friday-published reports."""
    M = market()
    s = published(M["spec"], 5, 1, 3)
    z = zscore(s, 252)
    f = forward(M["r"], 63) / (M["r"].std(0) * math.sqrt(252))
    out = {}
    for name, m in (("high", z > 1.5), ("low", z < -1.5), ("middle", np.abs(z) <= 1.5)):
        m = m & ~np.isnan(f)
        out[name] = (float(f[m].mean()), int(m.sum()))
    return out


@functools.lru_cache(maxsize=1)
def corn():
    with open(DATA / "cot_corn_disagg.csv") as fh:
        rows = list(csv.DictReader(fh))
    d = [dt.date.fromisoformat(r["date"]) for r in rows]
    pos = [{k: int(v) for k, v in r.items() if k != "date"} for r in rows]
    mm = np.array([net_share(p, "mm") for p in pos])
    pm = np.array([net_share(p, "pm") for p in pos])
    z = zscore(mm, 52)
    with open(DATA / "ags_monthly.csv") as fh:
        ag = list(csv.DictReader(fh))
    px = np.log(np.array([float(a["maize"]) for a in ag]))
    xs, ys, q = [], [], []
    for k, a in enumerate(ag[:-2]):
        y, mo = int(a["month"][:4]), int(a["month"][5:])
        end = dt.date(y, mo, calendar.monthrange(y, mo)[1])
        known = [i for i in range(len(d)) if d[i] + dt.timedelta(days=3) <= end]   # released by Friday
        if not known or np.isnan(z[known[-1]]):
            continue
        xs.append(z[known[-1]])
        ys.append(px[k + 2] - px[k + 1])
        if k + 4 < len(px):
            q.append((z[known[-1]], px[k + 4] - px[k + 1]))
    xs, ys, q = np.array(xs), np.array(ys), np.array(q)
    c = float(np.corrcoef(xs, ys)[0, 1])
    grp = {n: (float(q[m, 1].mean()), int(m.sum())) for n, m in
           (("high", q[:, 0] > 1), ("low", q[:, 0] < -1), ("middle", np.abs(q[:, 0]) <= 1))}
    return {"n": len(xs), "corr": c, "t": c * math.sqrt(len(xs)), "groups": grp,
            "mm_pm_corr": float(np.corrcoef(mm, pm)[0, 1]), "mm_range": (float(mm.min()), float(mm.max())),
            "dates": d, "mm": mm, "pm": pm}
