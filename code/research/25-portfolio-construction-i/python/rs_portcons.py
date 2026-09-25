"""Portfolio construction I (One Quant Book 7, chapter 25).

A long-short book of the 100 largest names of firm.synthmkt, rebuilt at each month's close from year 3 to year 10
by mean-variance optimisation (firm.portcons over firm.portopt). The alpha forecast is the simulation's stock-specific
expected return for the next month (its persistent drift and its post-earnings drift) plus noise, scaled by Grinold's
rule to an information coefficient (chapter 15); the risk model is chapter 24's fundamental model at a monthly
horizon. Constraints are added one at a time: dollar neutrality; beta, industry and style neutrality; name limits;
a gross limit; liquidity limits; a turnover limit. For each: the ex-ante information ratio and its decomposition by
constraint, the shadow prices, the realised information ratio over the following month's daily returns, turnover,
the transfer coefficient and the concentration of the book. NumPy only.
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
ROOT = HERE.parents[3] / "firm"
for c in ("portcons", "forecast"):
    sys.path.insert(0, str(ROOT / c))
sys.path.insert(0, str(HERE.parents[2] / "24-risk-models" / "python"))
from firm_forecast import transfer_coefficient  # noqa: E402
from firm_portcons import Problem  # noqa: E402
from rs_riskmodel import START, exposures, fundamental, market  # noqa: E402

MONTH, YEAR, N_NAMES = 21, 252, 100
NOISE, SEED = 2.0, 25
GAMMA, IC, SAMPLE = 12.0, 0.05, 126
NAME_LIMIT, GROSS, CAPITAL, PARTICIPATION, TURNOVER, COST = 0.03, 2.0, 1e9, 0.05, 0.5, 0.0010
SETTINGS = ("naive", "dollar neutral", "factor neutral", "name limits", "gross limit", "liquidity", "turnover limit")


def dates():
    P, R, _, _ = market()
    return list(range(START - 1, R.shape[0] - MONTH - 1, MONTH))


@functools.lru_cache(maxsize=1)
def forecasts():
    """{t0: (universe indices, alpha (n,), vol (n,), truth (n,))}: the monthly alpha forecast of each rebalance."""
    P, R, cap, _ = market()
    rng = np.random.default_rng(SEED)
    m = fundamental()
    out = {}
    for t0 in dates():
        c = np.where(P.listed[t0], np.nan_to_num(cap[t0]), -1.0)
        uni = np.sort(np.argsort(-c)[:N_NAMES])
        truth = MONTH * (np.nan_to_num(P.alpha["momentum"][t0, uni]) + np.nan_to_num(P.alpha["pead"][t0, uni]))
        f = truth + NOISE * truth.std() * rng.standard_normal(len(uni))
        z = (f - f.mean()) / f.std()
        spec = np.nan_to_num(m["spec"][t0, uni], nan=np.nanmedian(m["spec"][t0]))
        vol = np.sqrt(MONTH * spec)                                       # residual volatility, monthly
        out[t0] = (uni, IC * vol * z, vol, truth, IC * float(np.median(vol)) * z)
    return out


def risk(t0, uni):
    m = fundamental()
    X = exposures(t0 + 1)[uni]
    F = MONTH * m["covs"][t0] * m["lam2"][t0]
    spec = MONTH * np.nan_to_num(m["spec"][t0, uni], nan=np.nanmedian(m["spec"][t0]))
    return X, F, spec


def adv(t0, uni):
    P, _, _, _ = market()
    lo = max(0, t0 - MONTH + 1)
    dv = np.nan_to_num(P.price[lo:t0 + 1, uni] * P.volume[lo:t0 + 1, uni])
    return dv.mean(axis=0)


def build(level: int, t0: int, w0=None):
    """The problem with the first `level` + 1 settings, at rebalance t0. Level 0 (naive): alpha in return units (the
    same scale for every name) and the sample covariance of the last 126 days; from level 1 on, the alpha scaled by
    each name's residual volatility (chapter 15) and chapter 24's factor risk model."""
    uni, alpha, vol, _, raw = forecasts()[t0]
    n = len(uni)
    if level == 0:
        _, R, _, _ = market()
        S = MONTH * np.cov(np.nan_to_num(R[t0 - SAMPLE + 1:t0 + 1][:, uni]).T)
        p = Problem(raw, np.eye(n), S, np.zeros(n), GAMMA, w0=np.zeros(n) if w0 is None else w0)
        p.equality(np.ones(n), 0.0, "dollar neutral")
        return p
    X, F, spec = risk(t0, uni)
    p = Problem(alpha, X, F, spec, GAMMA, w0=np.zeros(n) if w0 is None else w0)
    p.equality(np.ones(n), 0.0, "dollar neutral")
    level = max(level - 1, 0)
    if level >= 1:
        names = ["beta"] + [f"industry {k}" for k in range(1, 11)] + ["size", "value", "momentum"]
        p.neutral_factors(list(range(1, X.shape[1])), names)
    if level >= 2:
        p.bounds(-NAME_LIMIT, NAME_LIMIT, "name limits")
    if level >= 3:
        p.gross(GROSS, "gross limit")
    if level >= 4:
        p.liquidity(adv(t0, uni), PARTICIPATION, CAPITAL, "liquidity")
    if level >= 5:
        p.turnover(TURNOVER, "turnover limit")
    return p


@functools.lru_cache(maxsize=8)
def run(level: int):
    """Month by month: the solution, its decomposition and its realised daily returns over the month."""
    P, R, _, _ = market()
    rows, prev = [], {}
    for t0 in dates():
        uni, alpha, vol, truth, _ = forecasts()[t0]
        w0 = np.array([prev.get(i, 0.0) for i in uni])
        p = build(level, t0, w0)
        res = p.solve()
        dec = p.ir_decomposition(res)
        w = res["w"]
        full_prev = sum(abs(v) for i, v in prev.items() if i not in set(uni.tolist()))
        daily = np.nan_to_num(R[t0 + 1:t0 + 1 + MONTH][:, uni]) @ w
        turn = float(np.abs(w - w0).sum() + full_prev)
        net = daily.copy()
        net[0] -= COST * turn                                            # 10 bp per unit of weight traded
        g = np.abs(w).sum()
        top2 = np.sort(np.abs(w))[-2:].sum() / g if g > 0 else 0.0
        rows.append({"t0": t0, "w": w, "uni": uni, "ir": res["ir"], "dec": dec, "duals": res["duals"],
                     "binding": res["binding"], "gross": g, "turnover": turn, "daily": daily, "net": net,
                     "tc": transfer_coefficient(w, alpha, vol), "top2": top2,
                     "risk": res["risk"], "status": res["status"]})
        prev = dict(zip(uni.tolist(), w.tolist(), strict=True))
    return rows


def summary(level: int):
    rows = run(level)
    daily = np.concatenate([r["daily"] for r in rows])
    net = np.concatenate([r["net"] for r in rows])
    ann = float(daily.mean() / daily.std(ddof=1) * math.sqrt(YEAR))
    ann_net = float(net.mean() / net.std(ddof=1) * math.sqrt(YEAR))
    ex = float(np.mean([r["ir"] for r in rows]) * math.sqrt(12))
    cost = float(-(net - daily).sum() / len(rows) * 12)
    return {"ir_ex_ante": ex, "ir_realised": ann, "ir_net": ann_net, "cost": cost,
            "turnover": float(np.mean([r["turnover"] for r in rows[1:]])),
            "gross": float(np.mean([r["gross"] for r in rows])), "tc": float(np.mean([r["tc"] for r in rows])),
            "top2": float(np.mean([r["top2"] for r in rows])), "top2_max": float(np.max([r["top2"] for r in rows])),
            "vol_pred": float(np.sqrt(np.mean([r["risk"] ** 2 for r in rows])) * math.sqrt(12)),
            "vol_real": float(daily.std(ddof=1) * math.sqrt(YEAR))}


def decomposition(level: int = 5):
    """The average share of the unconstrained ex-ante IR^2 removed by each constraint group, and the average shadow
    price of each named constraint."""
    rows = run(level)
    groups = {}
    for r in rows:
        free = r["dec"]["ir_free"] ** 2
        for k, v in r["dec"]["delta"].items():
            key = "factor neutral" if (k in ("beta", "size", "value", "momentum") or k.startswith("industry")) else k
            groups[key] = groups.get(key, 0.0) + v / free / len(rows)
    return groups
