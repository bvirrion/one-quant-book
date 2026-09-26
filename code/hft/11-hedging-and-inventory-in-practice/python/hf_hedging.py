"""Hedging and inventory in practice (One Quant Book 11, chapter 11).

Forty names, one factor, a day of client fills (firm.mmhedge.FlowDay: 46,000-odd fills of 100 shares, quotes skewed
against each name's inventory, clients selling into a falling market). Hedging rules compared on ten simulated
days: none, the future kept within half a contract of the exposure, the future outside a no-trade band, and the
single stocks traded back to a $20,000 band per name. Then the ten-to-four decision: flatten, sell the future
overnight, or keep, with Student-t overnight gaps.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "mmhedge"))
import firm_mmhedge as mh  # noqa: E402

DAYS = tuple(range(100, 110))
LAM = 1e-4                    # dollars of charge per squared dollar of daily variance
C_FUT, C_STK = 5e-5, 1.7e-4   # cost per dollar traded: future, single stocks
BANDS = (1e5, 2.5e5, 5e5, 1e6)
SF_NIGHT, SE_NIGHT = 0.006, 0.01
EOD_FROM, EOD_SKEW = 19800.0, 4.0   # 15:00, quotes skewed four times harder


@functools.cache
def day(seed: int) -> mh.FlowDay:
    return mh.FlowDay(seed=seed)


def _summary(rs) -> dict:
    risk = float(np.sqrt(np.mean([r["risk_min"] ** 2 for r in rs])) * np.sqrt(390.0))
    tot = float(np.mean([r["total"] for r in rs]))
    return {"cost": float(np.mean([r["hedge_cost"] for r in rs])), "risk": risk, "total": tot,
            "spread": float(np.mean([r["spread"] for r in rs])),
            "contracts": float(np.mean([r["contracts"] for r in rs])),
            "objective": tot - LAM * risk * risk}


@functools.cache
def frontier(c_fut: float = C_FUT) -> dict:
    """Mean hedge cost, intraday risk (one-minute P&L standard deviation scaled to a day), mean total and the
    mean-variance objective of each rule over the ten days."""
    out = {"none": _summary([mh.day_pnl(day(s), "none") for s in DAYS]),
           "future, zero": _summary([mh.day_pnl(day(s), "future zero", c_fut=c_fut) for s in DAYS])}
    for b in BANDS:
        out[f"future, band {b:,.0f}"] = _summary([mh.day_pnl(day(s), "future band", band=b, c_fut=c_fut) for s in DAYS])
    out["stocks"] = _summary([mh.day_pnl(day(s), "stocks", c_stk=C_STK) for s in DAYS])
    return out


def band(c_fut: float = C_FUT) -> dict:
    """The exposure's volatility and the no-trade band from firm.impulse at three risk aversions."""
    s = []
    for d in DAYS:
        Q = day(d).inventory()[0]
        D = np.sum(Q * day(d).p * day(d).beta, axis=1)
        s.append(np.diff(D).std() * np.sqrt(len(D)))
    sig = float(np.mean(s))
    return {"sigma_D": sig, "bands": {lam: mh.optimal_band(sig, lam, 0.01, c_fut) for lam in (1e-5, 3e-5, 1e-4)}}


def ten_to_four(seed: int = DAYS[0], n: int = 200000) -> dict:
    """The book at 15:50: the three choices over the night, and the overnight loss distribution of keeping it."""
    d = day(seed)
    t = d.m - int(round(600.0 / d.dt))
    q, p = d.inventory()[0][t], d.p[t]
    se = np.full(d.n, SE_NIGHT)
    gross = float(np.sum(np.abs(q) * p))
    D = mh.delta_equivalent(q, p, d.beta)
    flat = mh.flatten_cost(q, p, half_spread=d.hs, sigma=d.se)
    ch = mh.choose(q, p, d.beta, SF_NIGHT, se, 2 * C_FUT, flat / gross, LAM)
    out = {"gross": gross, "D": D, "flatten": flat, "future": 2 * C_FUT * abs(D), "choice": ch}
    for name, hedge in (("keep", 0.0), ("future", D)):
        loss = mh.overnight(q, p, d.beta, SF_NIGHT, se, hedge=hedge, n=n, seed=seed)
        v = np.quantile(loss, 0.99)
        out[name + "_sd"] = float(loss.std())
        out[name + "_var99"] = float(v)
        out[name + "_es99"] = float(loss[loss >= v].mean())
        out[name + "_hist"] = loss
    return out


@functools.cache
def eod() -> dict:
    """Flattening through the quotes from 15:00: gross book at the close, spread earned, flattening cost left."""
    out = {}
    for name, kw in (("normal", {}), ("skew from 15:00", {"eod_from": EOD_FROM, "eod_skew": EOD_SKEW})):
        rs = [mh.day_pnl(day(s), "none", **kw) for s in DAYS]
        gross = [float(np.sum(np.abs(r["q_end"]) * r["p_end"])) for r in rs]
        flat = [mh.flatten_cost(r["q_end"], r["p_end"], sigma=day(s).se) for r, s in zip(rs, DAYS, strict=True)]
        out[name] = {"gross": float(np.mean(gross)), "D": float(np.mean([abs(r["D_end"]) for r in rs])),
                     "spread": float(np.mean([r["spread"] for r in rs])), "flatten": float(np.mean(flat)),
                     "total": float(np.mean([r["total"] for r in rs]))}
    return out
