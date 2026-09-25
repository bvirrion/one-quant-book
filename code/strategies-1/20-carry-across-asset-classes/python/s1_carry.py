"""Carry across asset classes (One Quant Book 8, chapter 20).

firm.synthfut's forty futures (thirty years; half of each market's carry earned as expected excess return, or all of
it in a variant; in each stock crash, high-carry currencies lose 8% per unit of carry z-score). Carry is read from
the curve: the log slope between the first two monthly contracts (21 days apart), and for commodities also between
contracts twelve months apart (which cancels the seasonal cycle). Books per class, long high carry and short low
carry by rank, rebalanced daily at 2, 1, 2 and 4 basis points per unit traded by class, each scaled in sample to 10%
volatility; the diversified book gives each class the same weight and is scaled the same way. Measured: the curve
carry's correlation with the truth, Sharpe ratios by class and diversified, the books' returns in the three stock
crashes, the skewness of their monthly returns, the correlation with chapter 19's trend book, and carry on NYMEX WTI
crude oil (EIA, contracts 2 and 3, 1986-2024): its average, the share of days in backwardation, and a rule long in
backwardation and short in contango. NumPy only.
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
for p in ("synthfut", "carrystrat", "trendfollow", "bars"):
    sys.path.insert(0, str(ROOT / "firm" / p))
sys.path.insert(0, str(ROOT / "research" / "02-market-data-for-research" / "python"))
from firm_carrystrat import book, curve_carry, rank_weights, scale, skew_monthly, windows  # noqa: E402
from firm_synthfut import CLASSES, FutConfig, contracts, simulate_futures  # noqa: E402

COST_BP = (2.0, 1.0, 2.0, 4.0)
START, TARGET = 260, 0.10
WTI = ROOT.parent / "data" / "markets-3" / "wti_futures_c1_c4_daily.csv"


@functools.lru_cache(maxsize=2)
def market(premium: float = 0.5):
    F = simulate_futures(FutConfig(carry_premium=premium))
    T, N = F["r"].shape
    near = np.zeros((T, N))
    year = np.zeros((T, N))
    for t in range(T):
        k = contracts(F, t, 13, 21)
        near[t] = curve_carry(k[:, 0], k[:, 1], 21)
        year[t] = curve_carry(k[:, 0], k[:, 12], 252)
    F["carry_near"], F["carry_year"] = near, year
    F["cost"] = np.array(COST_BP)[F["cls"]] / 1e4
    return F


def sr(x):
    x = np.asarray(x)[START:]
    return float(x.mean() / x.std(ddof=1) * math.sqrt(252))


@functools.lru_cache(maxsize=8)
def books(signal: str = "near", premium: float = 0.5):
    """Per class P&L (scaled to 10%) and the diversified book (equal weights, scaled to 10%)."""
    F = market(premium)
    sig = F["carry_near"] if signal == "near" else F["carry_year"] if signal == "year" else F["carry"]
    if signal == "mixed":                                  # twelve-month slope for commodities, nearby elsewhere
        sig = np.where(F["cls"] == 3, F["carry_year"], F["carry_near"])
    w = rank_weights(sig, F["cls"])
    per = {}
    for k, name in enumerate(CLASSES):
        m = F["cls"] == k
        per[name] = scale(book(F["r"][:, m], w[:, m], F["cost"][m]), TARGET, START)
    div = scale(np.mean(list(per.values()), axis=0), TARGET, START)
    return per, div


def summary(signal: str = "mixed", premium: float = 0.5):
    per, div = books(signal, premium)
    F = market(premium)
    out = {name: {"sr": sr(x), "skew": skew_monthly(x, START), "crash": windows(x, F["crashes"])}
           for name, x in per.items()}
    out["diversified"] = {"sr": sr(div), "skew": skew_monthly(div, START), "crash": windows(div, F["crashes"])}
    return out


def carry_quality():
    """Correlation of curve carry with the true carry, all markets and the seasonal commodities."""
    F = market()
    s = F["amp"] > 0
    ns = ~s
    c = lambda a, b: float(np.corrcoef(a.ravel(), b.ravel())[0, 1])  # noqa: E731
    return {"near_all": c(F["carry_near"][:, ns], F["carry"][:, ns]),
            "near_seasonal": c(F["carry_near"][:, s], F["carry"][:, s]),
            "year_seasonal": c(F["carry_year"][:, s], F["carry"][:, s])}


def trend_correlation():
    from firm_trendfollow import ewma_vol, positions, run, tsmom
    F = market()
    p = np.mean([positions(tsmom(F["r"], L), ewma_vol(F["r"]), 0.4) for L in (21, 63, 252)], axis=0)
    trend = run(F["r"], p, F["cost"])
    _, div = books("mixed")
    return float(np.corrcoef(trend[START:], div[START:])[0, 1])


@functools.lru_cache(maxsize=1)
def wti():
    """Carry from contracts 2 and 3 (21 trading days apart in the model's convention: one month), the rolled series'
    returns, and a rule long in backwardation, short in contango (40% volatility target, 2 bp a trade)."""
    from firm_trendfollow import ewma_vol, positions, run
    from rs_marketdata import wti_series
    s = wti_series(5, start="1985-01-02")
    c23 = {}
    with open(WTI) as fh:
        for row in csv.DictReader(fh):
            c23[row["date"]] = math.log(float(row["c2"]) / float(row["c3"])) * 12
    carry = np.array([c23[d.isoformat()] for d in s["dates"]])
    r = np.diff(np.log(s["ratio"]))[:, None]
    sig = np.sign(carry[:-1])[:, None]
    p = positions(sig, ewma_vol(r), 0.4, 1)
    x = run(r, p, 2e-4)[START:]
    return {"mean_carry": float(carry.mean()), "backwardation": float((carry > 0).mean()),
            "sr": float(x.mean() / x.std(ddof=1) * math.sqrt(252)), "ret": float(x.mean() * 252),
            "years": (s["dates"][START + 1].year, s["dates"][-1].year), "carry": carry, "dates": s["dates"]}


def paths(premium: float = 0.5, step: int = 5):
    """Cumulative diversified and currency carry books (10% volatility) from START, every `step` days."""
    per, div = books("mixed", premium)
    cd, cf = np.cumsum(div[START:]), np.cumsum(per["currency"][START:])
    return [((START + i) / 252, float(cd[i]), float(cf[i])) for i in range(0, len(cd), step)]
