"""Anatomy of a stat-arb book (One Quant Book 8, chapter 1).

A daily long-short book on all the listed names of firm.synthmkt (seed 1): an equal blend of the residual one-day
reversal and 12-1 month momentum, both point in time, smoothed with a half-life of two days, weighted to gross
exposure three (1.5 long, 1.5 short), at most 1% of capital in a name, and made neutral to the market (beta), the ten
industries and the dollar, but not to the styles (or to the styles too); traded at the close for the next day with
costs of 5 basis points of the weight traded; financed at a prime broker with $1 billion of capital (benchmark rate
4%, long spread 0.5%, borrow fees by name with 5% of names hard to borrow, which are not shorted); every day's P&L
attributed with chapter 24 of Book 7's risk model. NumPy only.
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
for c in ("statbook", "features"):
    sys.path.insert(0, str(FIRM / c))
sys.path.insert(0, str(HERE.parents[3] / "research" / "24-risk-models" / "python"))
from firm_features import past_return  # noqa: E402
from firm_statbook import attribution, borrow_fees, financing, hard_to_borrow, reg_t_equity, stress_equity  # noqa: E402
from rs_riskmodel import START, exposures, fundamental, market  # noqa: E402

YEAR = 252
GROSS, COST, RATE, SPREAD, CAPITAL, HALF_LIFE, CAP = 3.0, 0.0005, 0.04, 0.005, 1e9, 2.0, 0.01
FACTORS = ["country"] + [f"industry {k}" for k in range(1, 11)] + ["beta", "size", "value", "momentum"]


def _z(x, ok):
    x = np.where(ok, x, np.nan)
    return np.nan_to_num((x - np.nanmean(x)) / np.nanstd(x))


@functools.lru_cache(maxsize=4)
def book(half_life: float = HALF_LIFE, neutral_styles: bool = False, seed: int = 8):
    """Daily weights (T, M): row t is decided at the close of t and held over t + 1."""
    P, R, cap, _ = market()
    m = fundamental()
    E = m["E"]
    T, M = R.shape
    mom = past_return(np.where(P.listed, P.ret, np.nan), YEAR - 21, 21)
    fees = borrow_fees(M, seed=seed)
    htb = hard_to_borrow(fees)
    lam = 0.5 ** (1.0 / half_life)
    W = np.zeros((T, M))
    s = np.zeros(M)
    for t in range(START - 1, T - 1):
        ok = P.listed[t] & np.isfinite(E[t]) & np.isfinite(mom[t])
        raw = 0.5 * _z(-E[t], ok) + 0.5 * _z(mom[t], ok)
        s = lam * s + (1 - lam) * raw
        X = exposures(t + 1)
        cols = list(range(12)) + ([12, 13, 14] if neutral_styles else [])
        live = ok & P.listed[t + 1]
        x = np.where(live, s, 0.0)
        Xl = X[live][:, cols]
        x[live] = x[live] - Xl @ np.linalg.lstsq(Xl, x[live], rcond=None)[0]
        x = np.where((x < 0) & htb, 0.0, x)                                # hard to borrow: not shorted
        w = x * GROSS / np.abs(x).sum()
        for _ in range(5):                                                  # at most 1% of capital in a name
            w = np.clip(w, -CAP, CAP)
            w = w * GROSS / np.abs(w).sum()
        W[t] = np.clip(w, -CAP, CAP)
    return W, fees


@functools.lru_cache(maxsize=4)
def run(half_life: float = HALF_LIFE, neutral_styles: bool = False):
    """Daily attribution rows over the evaluation days (fractions of capital)."""
    P, R, _, _ = market()
    m = fundamental()
    F, E = m["F"], m["E"]
    W, fees = book(half_life, neutral_styles)
    T = R.shape[0]
    rows = []
    prev = np.zeros(W.shape[1])
    for t in range(START - 1, T - 1):
        w = W[t]
        traded = float(np.abs(w - prev).sum())
        fin = financing(w, CAPITAL, RATE, SPREAD, fees)
        a = attribution(w, exposures(t + 1), F[t + 1], np.nan_to_num(E[t + 1]), COST * traded, fin["total"])
        a["pnl"] = float(np.nansum(w * np.nan_to_num(R[t + 1]))) - COST * traded + fin["total"]
        a["traded"], a["fin"] = traded, fin
        a["long"], a["short"] = float(w[w > 0].sum()), float(-w[w < 0].sum())
        a["n_long"], a["n_short"] = int((w > 0).sum()), int((w < 0).sum())
        rows.append(a)
        prev = w
    return rows


def summary(half_life: float = HALF_LIFE, neutral_styles: bool = False):
    rows = run(half_life, neutral_styles)
    tot = np.array([r["total"] for r in rows])
    pnl = np.array([r["pnl"] for r in rows])
    fac = np.array([r["factor"] for r in rows])
    spec = np.array([r["specific"] for r in rows])
    by = np.array([r["by_factor"] for r in rows])
    cost = np.array([r["cost"] for r in rows])
    fin = np.array([r["financing"] for r in rows])
    ann = lambda x: float(np.mean(x) * YEAR)  # noqa: E731
    vol = float(tot.std(ddof=1) * math.sqrt(YEAR))
    share = float(np.cov(fac, fac + spec)[0, 1] / np.var(fac + spec, ddof=1))
    return {"ret": ann(tot), "vol": vol, "sr": ann(tot) / vol, "gross_alpha": ann(spec + fac), "specific": ann(spec),
            "factor": ann(fac), "cost": ann(cost), "financing": ann(fin), "factor_var_share": share,
            "check": float(np.abs(tot - pnl).max()),
            "by_factor": {FACTORS[k]: ann(by[:, k]) for k in range(by.shape[1])},
            "by_factor_vol": {FACTORS[k]: float(by[:, k].std() * math.sqrt(YEAR)) for k in range(by.shape[1])},
            "turnover": float(np.mean([r["traded"] for r in rows[1:]])) / 2,
            "n_long": float(np.mean([r["n_long"] for r in rows])),
            "n_short": float(np.mean([r["n_short"] for r in rows])),
            "best": float(tot.max()), "worst": float(tot.min()),
            "long_cost": -ann(np.array([r["fin"]["long_cost"] for r in rows])),
            "rebate": ann(np.array([r["fin"]["short_rebate"] for r in rows])),
            "borrow": -ann(np.array([r["fin"]["borrow_cost"] for r in rows]))}


def margin_example():
    """Reg T and a 15% stress requirement for the book's gross, per $1 of capital."""
    return reg_t_equity(GROSS / 2, -GROSS / 2), stress_equity(np.r_[GROSS / 2, -GROSS / 2], 1.0, 0.15)


def bets(neutral_styles: bool = True):
    """Position-days held and the largest single weight over the evaluation days."""
    W, _ = book(HALF_LIFE, neutral_styles)
    rows = W[START - 1:-1]
    return int((rows != 0).sum()), float(np.abs(rows).max()), float(np.median(np.abs(rows[rows != 0])))
