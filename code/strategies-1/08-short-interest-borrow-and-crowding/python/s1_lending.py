"""Short interest, borrow and crowding (One Quant Book 8, chapter 8).

A lending market on firm.synthmkt (seed 1): informed short sellers follow each stock's planted expected return (20-day
half-life), uninformed shorts are persistent noise, supply is a lognormal share of each stock's shares, fees rise
steeply above 60% utilisation. Over years 3 to 10: the rank IC of short interest, days to cover, the fee and a
crowding score against the next month's return; a monthly decile book short the most-shorted and long the
least-shorted names (gross 1) before and after borrow fees and 10 basis points per unit traded; the long-only market
without its most-shorted decile; and a squeeze stress on the 20 most crowded names. NumPy only.
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

HERE = pathlib.Path(__file__).resolve()
FIRM = HERE.parents[3] / "firm"
for c in ("lendsig", "factorlib", "predictor", "synthmkt"):
    sys.path.insert(0, str(FIRM / c))
from firm_factorlib import sort_book  # noqa: E402
from firm_lendsig import LendingConfig, crowding, days_to_cover, simulate_lending, squeeze_loss  # noqa: E402
from firm_predictor import ic_series  # noqa: E402
from firm_synthmkt import simulate  # noqa: E402

YEAR, MONTH, START, COST, CROWD = 252, 21, 504, 0.0010, 20


@functools.lru_cache(maxsize=1)
def market():
    P = simulate()
    R = np.where(P.listed, P.ret, np.nan)
    alpha = sum(np.nan_to_num(v) for v in P.alpha.values())
    lend = simulate_lending(alpha, P.listed, P.shares[0], LendingConfig())
    vol = np.where(P.listed, P.volume, 0.0)
    c = np.cumsum(vol, axis=0)
    adv = (c - np.vstack([np.zeros((21, vol.shape[1])), c[:-21]])) / 21
    shares = np.where(P.listed, P.shares, np.nan)
    dtc = days_to_cover(lend["si"], shares, adv)
    lr2 = np.cumsum(np.log1p(np.nan_to_num(R)) ** 2, axis=0)
    sig = np.sqrt(np.maximum((lr2 - np.vstack([np.zeros((63, lr2.shape[1])), lr2[:-63]])) / 63, 1e-8))
    return P, R, lend, adv, shares, dtc, sig


def _fwd(R, h=MONTH):
    lr = np.log1p(R)
    c = np.concatenate([np.zeros((1, R.shape[1])), np.cumsum(np.nan_to_num(lr), axis=0)])
    y = np.full(R.shape, np.nan)
    T = R.shape[0]
    y[:T - h] = c[h + 1:] - c[1:T - h + 1]
    return y


def signal(name: str):
    P, R, lend, adv, shares, dtc, _ = market()
    if name == "si":
        return lend["si"]
    if name == "dtc":
        return dtc
    if name == "fee":
        return lend["fee"]
    return crowding(lend["si"], lend["util"], dtc)


def ic(name: str) -> float:
    """Mean rank IC of minus the signal (heavily shorted = low expected return) against the next month's return."""
    P, R, *_ = market()
    rows = np.arange(START, R.shape[0] - MONTH, MONTH)
    y = _fwd(R)
    return float(np.nanmean(ic_series(-signal(name)[rows], np.where(P.listed[rows + MONTH], y[rows], np.nan))))


def sharpe(x) -> float:
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * math.sqrt(YEAR))


@functools.lru_cache(maxsize=8)
def book(name: str = "si"):
    """Monthly decile book short the highest signal, long the lowest; daily gross, fee and cost (fractions)."""
    P, R, lend, *_ = market()
    s = -signal(name)
    W = sort_book(s, P.listed & np.isfinite(s))
    W = W[(np.arange(len(W)) // MONTH) * MONTH]
    r = np.nan_to_num(R)
    gross = np.sum(W[:-1] * r[1:], axis=1)
    fee = np.sum(np.where(W[:-1] < 0, -W[:-1], 0.0) * np.nan_to_num(lend["fee"][:-1]), axis=1) / YEAR
    traded = np.r_[np.abs(W[0]).sum(), np.abs(np.diff(W, axis=0)).sum(axis=1)][:-1]
    g, f, c = gross[START - 1:], fee[START - 1:], COST * traded[START - 1:]
    short_fee = np.nanmean(np.where(W[START:] < 0, lend["fee"][START:], np.nan))
    return {"sr_gross": sharpe(g), "sr_fee": sharpe(g - f), "sr_net": sharpe(g - f - c),
            "ret_gross": float(g.mean() * YEAR), "fee": float(f.mean() * YEAR), "cost": float(c.mean() * YEAR),
            "short_fee": float(short_fee),
            "net": g - f - c, "gross": g, "after_fee": g - f}


@functools.lru_cache(maxsize=1)
def avoidance():
    """Equal-weighted long-only market, and the same without its most-shorted decile, rebuilt monthly."""
    P, R, lend, *_ = market()
    si = lend["si"]
    r = np.nan_to_num(R)
    out = {"all": [], "avoid": []}
    for t in range(START - 1, R.shape[0] - 1):
        m = (t // MONTH) * MONTH
        ok = P.listed[m] & np.isfinite(si[m]) & P.listed[t]
        cut = np.nanpercentile(si[m, ok], 90)
        keep = ok & (si[m] < cut)
        out["all"].append(r[t + 1, ok].mean())
        out["avoid"].append(r[t + 1, keep].mean())
    a, b = np.array(out["all"]), np.array(out["avoid"])
    return {"all": float(a.mean() * YEAR), "avoid": float(b.mean() * YEAR), "diff": float((b - a).mean() * YEAR),
            "t": float((b - a).mean() / (b - a).std(ddof=1) * math.sqrt(len(a)))}


def levels():
    """Cross-sectional distribution of short interest, utilisation and fees over the evaluation days."""
    P, R, lend, adv, shares, dtc, _ = market()
    x = lend["si"][START:]
    u, f, d = lend["util"][START:], lend["fee"][START:], dtc[START:]
    return {"si_median": float(np.nanmedian(x)), "si_p90": float(np.nanpercentile(x, 90)),
            "si_max": float(np.nanmax(x)),
            "util_p90": float(np.nanpercentile(u, 90)), "fee_hot": float(np.nanmean(f > 0.01)),
            "fee_p99": float(np.nanpercentile(f, 99)), "dtc_median": float(np.nanmedian(d)),
            "dtc_p90": float(np.nanpercentile(d, 90))}


@functools.lru_cache(maxsize=4)
def squeeze(cover: float = 0.5, days: int = 5):
    """At each month-end, a book short the CROWD most crowded names (-0.5 of capital, equal weights): the loss if a
    share `cover` of each name's short interest is bought back over `days` days, against the book's worst actual
    5-day loss over the sample."""
    P, R, lend, adv, shares, dtc, sig = market()
    cr = signal("crowding")
    losses, actual = [], []
    r = np.nan_to_num(R)
    for t in range(START, R.shape[0] - days, MONTH):
        ok = P.listed[t] & np.isfinite(cr[t])
        idx = np.flatnonzero(ok)[np.argsort(-cr[t, ok])[:CROWD]]
        w = np.full(len(idx), -0.5 / CROWD)
        losses.append(squeeze_loss(w, lend["si"][t, idx], shares[t, idx], adv[t, idx], sig[t, idx], cover, days))
        actual.append(float(w @ (np.prod(1 + r[t + 1:t + 1 + days, idx], axis=0) - 1)))
    L, A = np.array(losses), np.array(actual)
    return {"median": float(np.median(L)), "worst": float(L.min()), "actual_worst": float(A.min()),
            "actual_median": float(np.median(A)), "n": len(L), "losses": L, "actual": A}
