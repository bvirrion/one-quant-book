"""Value, quality and low risk (One Quant Book 8, chapter 6).

On firm.synthmkt (seed 1), years 3 to 10, decile long-short books (gross 1, equal weights) with 10 basis points per unit
traded: value from book-to-price timed four ways (the book as filed with today's price, rebuilt monthly; the same
rebuilt once a year; the Fama-French convention, a book at least six months old with the price of its own date, rebuilt
once a year; and a look-ahead version using each book from its fiscal end, before it was filed); profitability (four
times quarterly earnings over book, as filed); betting against beta on Book 7 chapter 24's trailing betas (quintiles,
each side scaled to a beta of one); the beta deciles' realised returns; and a composite of value and momentum. The
synthetic market plants a value premium on the current book-to-price and a market premium proportional to beta, and no
profitability or low-risk premium. NumPy only.
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
for c in ("factorlib", "momstrat", "vecbt", "predictor"):
    sys.path.insert(0, str(FIRM / c))
sys.path.insert(0, str(HERE.parents[3] / "research" / "24-risk-models" / "python"))
from firm_factorlib import bab_book, book_to_price, composite, sort_book  # noqa: E402
from firm_momstrat import total_mom  # noqa: E402
from firm_predictor import ic_series  # noqa: E402
from firm_vecbt import backtest  # noqa: E402
from rs_riskmodel import START, betas, market  # noqa: E402

YEAR, MONTH, COST, LAG, JUNE = 252, 21, 0.0010, 126, 126


@functools.lru_cache(maxsize=1)
def cum():
    P, R, _, _ = market()
    return np.cumsum(np.log1p(np.where(P.listed, np.nan_to_num(R), 0.0)), axis=0)


@functools.lru_cache(maxsize=4)
def anchors(when: str):
    """log(B / P) + cum at the day the book is used: 'filed', 'fiscal' (look-ahead) or 'ff' (six months after the
    fiscal end, a stand-in for the Fama-French June rule)."""
    P, _, _, _ = market()
    T, M = P.ret.shape
    c = cum()
    split = {(t, p): r for t, p, r in P.splits}
    A = np.full((T, M), np.nan)
    for f in P.fundamentals:
        if f["field"] != "book":
            continue
        p, fe = f["pid"], f["fiscal_end"]
        day = {"filed": f["filed"], "fiscal": fe, "ff": max(fe + LAG, f["filed"])}[when]
        px = P.price[fe, p] / split.get((fe, p), 1)
        if day < T and np.isfinite(px) and px > 0:
            A[day, p] = math.log(f["value"] / px) + c[fe, p]
    return A


@functools.lru_cache(maxsize=8)
def value_signal(variant: str):
    P, _, _, _ = market()
    if variant == "ff":
        return book_to_price(anchors("ff"), cum(), P.listed, current=False)
    return book_to_price(anchors("fiscal" if variant == "lookahead" else "filed"), cum(), P.listed, current=True)


@functools.lru_cache(maxsize=1)
def profitability():
    """4 x the latest filed quarterly EPS over the latest filed book (per share), known from their filing days."""
    P, _, _, _ = market()
    T, M = P.ret.shape
    out = {}
    for field in ("eps", "book"):
        A = np.full((T, M), np.nan)
        for f in P.fundamentals:
            if f["field"] == field and f["filed"] < T:
                A[f["filed"], f["pid"]] = f["value"]
        idx = np.maximum.accumulate(np.where(np.isfinite(A), np.arange(T)[:, None], 0), axis=0)
        out[field] = A[idx, np.arange(M)[None, :]]
    return np.where(P.listed, 4 * out["eps"] / out["book"], np.nan)


def sharpe(x) -> float:
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * math.sqrt(YEAR))


def _hold(W, every: int, offset: int = 0):
    idx = np.maximum(((np.arange(len(W)) - offset) // every) * every + offset, 0)
    return W[idx]


@functools.lru_cache(maxsize=16)
def run(name: str):
    """Daily net returns (after 10 bp per unit traded) over the evaluation days, and summary statistics."""
    P, R, _, mkt = market()
    uni = P.listed
    if name in ("value", "value_annual", "ff", "lookahead"):
        s = value_signal("ff" if name == "ff" else "lookahead" if name == "lookahead" else "pit")
        W = sort_book(s, uni & np.isfinite(s))
        W = _hold(W, YEAR, JUNE) if name in ("value_annual", "ff") else _hold(W, MONTH)
    elif name == "profitability":
        s = profitability()
        W = _hold(sort_book(s, uni & np.isfinite(s)), MONTH)
    elif name == "bab":
        W = _hold(bab_book(betas(), uni), MONTH)
    else:                                                        # composite of value and momentum
        s = composite(value_signal("pit"), np.where(uni, total_mom(R), np.nan))
        W = _hold(sort_book(s, uni & np.isfinite(s)), MONTH)
    res = backtest(W, np.where(P.listed, R, np.nan), lag=1, cost=COST)
    n = res.net[START:]
    m = mkt[START:]
    beta = float(np.cov(m, n)[0, 1] / m.var(ddof=1))
    alpha = float((n.mean() - beta * m.mean()) * YEAR)
    return {"net": n, "sr": sharpe(n), "ret": float(n.mean() * YEAR), "vol": float(n.std(ddof=1) * math.sqrt(YEAR)),
            "beta": beta, "alpha": alpha, "turnover": float(res.turnover[START:].sum() / (len(n) / YEAR))}


def ic(signal) -> float:
    """Mean rank IC of a signal against the planted value alpha (the truth), over the evaluation days, monthly."""
    P, _, _, _ = market()
    rows = np.arange(START, P.ret.shape[0] - 1, MONTH)
    return float(np.nanmean(ic_series(np.asarray(signal)[rows], P.alpha["value"][rows])))


def sml():
    """Mean annual return and realised beta of the ten trailing-beta deciles (equal weights, rebuilt monthly)."""
    P, R, _, mkt = market()
    B = betas()
    out = []
    for d in range(10):
        W = np.zeros(B.shape)
        for t in range(0, B.shape[0], MONTH):
            ok = P.listed[t]
            b = np.where(ok, B[t], np.nan)
            lo, hi = np.nanpercentile(b, [10 * d, 10 * (d + 1)])
            sel = ok & (b >= lo) & (b <= hi)
            W[t:t + MONTH, sel] = 1.0 / sel.sum()
        r = np.nansum(W[START - 1:-1] * np.nan_to_num(R[START:]), axis=1)
        m = mkt[START:]
        out.append({"decile": d + 1, "ret": float(r.mean() * YEAR), "beta": float(np.cov(m, r)[0, 1] / m.var(ddof=1))})
    return out


def correlations():
    names = ("value", "profitability", "bab", "composite")
    from_mom = HERE.parents[2] / "05-momentum" / "python"
    sys.path.insert(0, str(from_mom))
    from s1_momentum import book as mom_book
    x = {k: run(k)["net"] for k in names}
    x["momentum"] = mom_book("total")["net"]
    c = lambda a, b: float(np.corrcoef(x[a], x[b])[0, 1])  # noqa: E731
    return {"value_profitability": c("value", "profitability"), "value_momentum": c("value", "momentum"),
            "value_bab": c("value", "bab")}
