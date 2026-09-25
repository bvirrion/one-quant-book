"""Trend following (One Quant Book 8, chapter 19).

firm.synthfut's thirty years of forty futures (equity indices, bonds, currencies, commodities; planted drifts with a
one-year half-life, carry, volatility clustering, three stock crashes), traded with firm.trendfollow's signal families
at three speeds each: the sign of the past 1-, 3- and 12-month return; moving-average crossovers 5/20, 20/100 and
50/250 days; breakouts of 20, 55 and 250 days. Each market targets 40% annual volatility divided by the number of
markets, from an exponentially weighted volatility forecast (centre of mass 60 days); costs are 2, 1, 2 and 4 basis
points per unit of notional traded by class (assumed). Measured: Sharpe ratios after costs by signal and speed, the
blend of speeds, equal-notional against volatility-scaled positions, the blend under a 10% portfolio volatility
target, its return in each stock crash, its quarterly returns against the equity class's (the smile), its Sharpe
ratio decade by decade, and the 12-month rule on NYMEX WTI crude oil (EIA, 1985-2024, rolled five days before
expiry). NumPy only.
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
sys.path.insert(0, str(ROOT / "firm" / "synthfut"))
sys.path.insert(0, str(ROOT / "firm" / "trendfollow"))
sys.path.insert(0, str(ROOT / "firm" / "bars"))
sys.path.insert(0, str(ROOT / "research" / "02-market-data-for-research" / "python"))
from firm_synthfut import simulate_futures  # noqa: E402
from firm_trendfollow import breakout, ewma_vol, ma_cross, positions, run, tsmom, vol_target  # noqa: E402

COST_BP = (2.0, 1.0, 2.0, 4.0)
TARGET, BOOK_VOL, START = 0.4, 0.10, 260
SPEEDS = {"return": (21, 63, 252), "ma": ((5, 20), (20, 100), (50, 250)), "breakout": (20, 55, 250)}


@functools.lru_cache(maxsize=1)
def market():
    F = simulate_futures()
    F["cost"] = np.array(COST_BP)[F["cls"]] / 1e4
    F["ewma"] = ewma_vol(F["r"])
    return F


def sr(x):
    x = np.asarray(x)[START:]
    return float(x.mean() / x.std(ddof=1) * math.sqrt(252))


@functools.lru_cache(maxsize=16)
def pos(family: str, k: int, scaled: bool = True):
    F = market()
    r, L = F["r"], SPEEDS[family][k]
    sig = tsmom(r, L) if family == "return" else ma_cross(r, *L) if family == "ma" else breakout(r, L)
    vol = F["ewma"] if scaled else np.full(r.shape, 0.15)
    return positions(sig, vol, TARGET)


def pnl(p):
    F = market()
    return run(F["r"], p, F["cost"])


def table():
    """Sharpe ratio after costs, annual turnover (notional traded / mean gross) and gross Sharpe ratio by family and
    speed."""
    out = {}
    for fam in SPEEDS:
        for k in range(3):
            p = pos(fam, k)
            turn = np.abs(np.diff(p[START:], axis=0)).sum() / np.abs(p[START:]).sum(1).mean() / (len(p) - START) * 252
            out[(fam, k)] = (sr(pnl(p)), float(turn), sr(run(market()["r"], p, 0.0)))
    return out


@functools.lru_cache(maxsize=4)
def blend(scaled: bool = True, families: tuple = ("return",)):
    p = np.mean([pos(f, k, scaled) for f in families for k in range(3)], axis=0)
    return pnl(p)


def summary():
    b, e = blend(), blend(True, tuple(SPEEDS))
    v = vol_target(b, BOOK_VOL)
    u = blend(False)
    return {"blend": sr(b), "all9": sr(e), "equal_notional": sr(u), "targeted": sr(v),
            "vol_blend": float(b[START:].std() * math.sqrt(252)),
            "vol_targeted": float(v[START:].std() * math.sqrt(252)),
            "dd_blend": maxdd(b / b[START:].std()), "dd_targeted": maxdd(v / v[START:].std())}


def maxdd(x):
    c = np.cumsum(np.asarray(x)[START:])
    return float((np.maximum.accumulate(c) - c).max() / math.sqrt(252))   # in annual standard deviations


def crises():
    """Per stock crash: the equity class's mean cumulative return and the blend's (scaled to 10% volatility)."""
    F, b = market(), vol_target(blend(), BOOK_VOL)
    eq = F["r"][:, F["cls"] == 0].mean(1)
    return [(float(np.expm1(eq[s:e].sum())), float(b[s:e].sum())) for s, e in F["crashes"]]


def smile(q: int = 63):
    F, b = market(), vol_target(blend(), BOOK_VOL)
    eq = F["r"][:, F["cls"] == 0].mean(1)
    idx = range(START, len(b) - q + 1, q)
    x = np.array([eq[i:i + q].sum() for i in idx])
    y = np.array([b[i:i + q].sum() for i in idx])
    coef = np.polyfit(x, y, 2)
    return x, y, coef


def decades():
    b = vol_target(blend(), BOOK_VOL)
    return [float(b[s:s + 2520].mean() / b[s:s + 2520].std(ddof=1) * math.sqrt(252)) for s in (START, 2520, 5040)]


@functools.lru_cache(maxsize=1)
def wti():
    """12-month time-series momentum on WTI (ratio-adjusted continuous series), volatility-scaled, 2 bp a trade."""
    from rs_marketdata import wti_series
    s = wti_series(5, start="1985-01-02")
    r = np.diff(np.log(s["ratio"]))[:, None]
    p = positions(tsmom(r, 252), ewma_vol(r), TARGET, 1)
    x = run(r, p, 2e-4)[START:]
    h = r[START:, 0]
    yrs = [d.year for d in s["dates"][1:]][START:]
    return {"sr": float(x.mean() / x.std(ddof=1) * math.sqrt(252)), "ret": float(x.mean() * 252),
            "hold_sr": float(h.mean() / h.std(ddof=1) * math.sqrt(252)), "first": yrs[0], "last": yrs[-1],
            "long_share": float((p[START:-1, 0] > 0).mean())}


def lookbacks(months=(1, 2, 3, 6, 9, 12, 18, 24)):
    """Sharpe ratio after costs of the volatility-scaled sign-of-return rule by lookback in months (21 days)."""
    F = market()
    return [(m, sr(pnl(positions(tsmom(F["r"], 21 * m), F["ewma"], TARGET)))) for m in months]


def paths(step: int = 5):
    """Cumulative trend book (10% volatility target) and equity class mean, from START, every `step` days."""
    F, b = market(), vol_target(blend(), BOOK_VOL)
    eq = F["r"][:, F["cls"] == 0].mean(1)
    cb, ce = np.cumsum(b[START:]), np.cumsum(eq[START:])
    return [((START + i) / 252, float(cb[i]), float(ce[i])) for i in range(0, len(cb), step)]
