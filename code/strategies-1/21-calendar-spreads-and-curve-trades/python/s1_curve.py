"""Calendar spreads and curve trades (One Quant Book 8, chapter 21).

NYMEX WTI crude oil (EIA daily settlements of contracts 1 to 4, 1985-2024): the calendar spread long the nearer and
short the farther of the nearest pair clear of expiry (contracts 1-2, moving to 2-3 five trading days before the
nearby expires), tracked by contract identity through each expiry. The log spread's daily persistence; a mean-reversion
rule that enters against a 20-day z-score beyond 1.5 and leaves inside 0.5 (or when it changes sign), sized at entry to
10% annual volatility from an EWMA forecast of the spread's dollar P&L, at one cent a barrel per unit traded (assumed);
a storage filter that forbids and closes long spreads when the pair's annualised carry is below a threshold. Measured
over 1986-2019 (gross and net Sharpe ratios) and in 2020. On firm.synthfut's ten commodities: the log spread between
the nearby and the contract twelve months out, traded against its 252-day z-score, daily or monthly, at 4 basis points
per leg per unit traded. NumPy only.
"""
from __future__ import annotations

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
for p in ("curvestrat", "trendfollow", "synthfut", "bars"):
    sys.path.insert(0, str(ROOT / "firm" / p))
sys.path.insert(0, str(ROOT / "research" / "02-market-data-for-research" / "python"))
from firm_curvestrat import band, pair_pnl, serials, spread_carry, zscore  # noqa: E402
from firm_synthfut import contracts, simulate_futures  # noqa: E402
from firm_trendfollow import ewma_vol  # noqa: E402

WTI = ROOT.parent / "data" / "markets-3" / "wti_futures_c1_c4_daily.csv"
TICK, WINDOW, ENTER, LEAVE, TARGET = 0.01, 20, 1.5, 0.5, 0.10


@functools.lru_cache(maxsize=1)
def wti():
    from rs_marketdata import wti_expiries
    with open(WTI) as fh:
        rows = list(csv.DictReader(fh))
    d = [dt.date.fromisoformat(r["date"]) for r in rows]
    C = np.array([[float(r[k]) for k in ("c1", "c2", "c3", "c4")] for r in rows])
    exp = wti_expiries(d)
    pnl, spread = pair_pnl(C, serials(exp), 0, 5, exp)
    return {"dates": d, "pnl": pnl, "spread": spread, "carry": spread_carry(spread),
            "vol": ewma_vol(pnl[:, None])[:, 0]}


def persistence():
    x = wti()["spread"]
    x = x[~np.isnan(x)]
    phi = float(np.corrcoef(x[1:], x[:-1])[0, 1])
    return phi, math.log(0.5) / math.log(phi)


@functools.lru_cache(maxsize=8)
def book(threshold: float | None = None):
    w = wti()
    block = None if threshold is None else w["carry"] < threshold
    p = band(zscore(w["spread"], WINDOW), w["vol"], ENTER, LEAVE, TARGET, block)
    gross = np.zeros(len(p))
    gross[1:] = p[:-1] * w["pnl"][1:]
    net = gross - TICK * np.abs(np.diff(p, prepend=0.0))
    yr = np.array([d.year for d in w["dates"]])
    mo = np.array([d.month for d in w["dates"]])
    pre = (yr >= 1986) & (yr <= 2019)
    s = lambda x: float(x.mean() / x.std(ddof=1) * math.sqrt(252))  # noqa: E731
    return {"gross": s(gross[pre]), "net": s(net[pre]), "ret": float(net[pre].mean() * 252),
            "vol": float(net[pre].std() * math.sqrt(252)), "active": float((p[pre] != 0).mean()),
            "y2020": float(net[yr == 2020].sum()), "mar": float(net[(yr == 2020) & (mo == 3)].sum()),
            "apr": float(net[(yr == 2020) & (mo == 4)].sum()), "net_series": net, "pos": p}


@functools.lru_cache(maxsize=4)
def synthetic(window: int = 252, monthly: bool = True):
    F = simulate_futures()
    com = np.flatnonzero(F["cls"] == 3)
    T = len(F["r"])
    sl = np.array([contracts(F, t, 13, 21)[com][:, 0] - contracts(F, t, 13, 21)[com][:, 12] for t in range(T)])
    pnl = np.diff(sl, axis=0, prepend=sl[:1])                  # equals the change in carry in this model
    z = np.column_stack([zscore(sl[:, j], window) for j in range(len(com))])
    vol = pnl[1:].std(axis=0) * math.sqrt(252)
    p = -np.clip(np.nan_to_num(z), -2, 2) / vol / len(com) * TARGET
    if monthly:
        p = p[np.arange(T) // 21 * 21]
    gross = np.zeros(T)
    gross[1:] = (p[:-1] * pnl[1:]).sum(1)
    net = gross - (np.abs(np.diff(p, axis=0, prepend=0.0)) * 8e-4).sum(1)
    s = lambda x: float(x[2 * 260:].mean() / x[2 * 260:].std(ddof=1) * math.sqrt(252))  # noqa: E731
    dc = np.diff(F["carry"][:, com], axis=0)
    return {"gross": s(gross), "net": s(net), "corr_dc": float(np.corrcoef(pnl[1:].ravel(), dc.ravel())[0, 1])}
