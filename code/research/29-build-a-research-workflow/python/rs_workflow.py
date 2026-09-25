"""Build a research workflow (One Quant Book 7, chapter 29).

The book's reference study as a firm.workflow pipeline: a snapshot of firm.synthmkt (the vendor's data, with any
revisions the vendor has made), the liquid universe, two features (12-1 momentum and the one-day reversal), their
predictor-card statistics (mean daily rank IC and its t statistic), a blend, a monthly dollar-neutral book, a level-1
backtest with costs, and a tear sheet with a bootstrap interval for the Sharpe ratio. Runs in a content-addressed
cache; vendor revisions, parameter changes and a missing seed show which stages recompute and what reproduces.
NumPy only.
"""
from __future__ import annotations

import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("workflow", "synthmkt", "features", "vecbt", "perf", "researchlog"):
    sys.path.insert(0, str(ROOT / c))
from firm_features import past_return  # noqa: E402
from firm_perf import sharpe  # noqa: E402
from firm_synthmkt import MarketConfig, simulate  # noqa: E402
from firm_vecbt import backtest, signal_to_weights  # noqa: E402
from firm_workflow import Pipeline, Stage  # noqa: E402

YEAR, MONTH = 252, 21


def snapshot(inputs, params, seed):
    P = simulate(MarketConfig(seed=params["market_seed"]))
    ret = np.where(P.listed, P.ret, np.nan)
    for day, pid, value in params["revisions"]:
        ret[day, pid] = value
    return {"ret": ret, "listed": P.listed, "dollar_volume": np.where(P.listed, P.price * P.volume, 0.0)}


def universe(inputs, params, seed):
    dv = inputs["snapshot"]["dollar_volume"]
    c = np.cumsum(dv, axis=0)
    w = params["window"]
    avg = (c - np.vstack([np.zeros((w, dv.shape[1])), c[:-w]])) / w
    rank = np.argsort(np.argsort(-avg, axis=1), axis=1)
    return (rank < params["top"]) & inputs["snapshot"]["listed"]


def features(inputs, params, seed):
    ret, uni = inputs["snapshot"]["ret"], inputs["universe"]
    mom = past_return(ret, YEAR - MONTH, MONTH)
    rev = -np.nan_to_num(ret)
    return {"momentum": np.where(uni, mom, np.nan), "reversal": np.where(uni, rev, np.nan)}


def _rank_ic(x, y):
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 20:
        return np.nan
    a, b = np.argsort(np.argsort(x[ok])), np.argsort(np.argsort(y[ok]))
    return float(np.corrcoef(a, b)[0, 1])


def cards(inputs, params, seed):
    ret = inputs["snapshot"]["ret"]
    out = {}
    for name, f in inputs["features"].items():
        ic = np.array([_rank_ic(f[t], ret[t + 1]) for t in range(YEAR, len(ret) - 1)])
        ic = ic[np.isfinite(ic)]
        out[name] = {"ic": float(ic.mean()), "t": float(ic.mean() / ic.std(ddof=1) * np.sqrt(len(ic))), "days": len(ic)}
    return out


def blend(inputs, params, seed):
    out = 0.0
    for name, w in params["weights"].items():
        f = inputs["features"][name]
        z = (f - np.nanmean(f, axis=1, keepdims=True)) / np.nanstd(f, axis=1, keepdims=True)
        out = out + w * np.nan_to_num(z)
    return np.where(inputs["universe"], out, np.nan)


def portfolio(inputs, params, seed):
    w = signal_to_weights(np.nan_to_num(inputs["blend"]), inputs["universe"], gross=params["gross"])
    return w[(np.arange(len(w)) // params["rebalance"]) * params["rebalance"]]


def level1(inputs, params, seed):
    res = backtest(inputs["portfolio"], inputs["snapshot"]["ret"], lag=params["lag"], cost=params["cost"])
    return {"net": res.net, "turnover": res.turnover}


def tearsheet(inputs, params, seed):
    x = inputs["level1"]["net"][YEAR:]
    rng = np.random.default_rng(seed)
    n, b = len(x), params["block"]
    boots = []
    for _ in range(params["reps"]):
        starts = rng.integers(0, n - b, n // b)
        boots.append(sharpe(np.concatenate([x[s:s + b] for s in starts]))["sr"])
    s = sharpe(x)
    lo, hi = np.quantile(boots, [0.025, 0.975])
    return {"sr": s["sr"], "se_iid": s["se_iid"], "lo": float(lo), "hi": float(hi),
            "turnover": float(np.mean(inputs["level1"]["turnover"][YEAR:]))}


def tearsheet_v2(inputs, params, seed):
    """The tear sheet after a code change: the same statistics and the hit rate."""
    out = tearsheet(inputs, params, seed)
    x = inputs["level1"]["net"][YEAR:]
    out["hit_rate"] = float(np.mean(x[x != 0] > 0))
    return out


def make(revisions=(), weights=None, seed=7, reps=200, tear=tearsheet):
    weights = weights or {"momentum": 0.5, "reversal": 0.5}

    def build(cache):
        return Pipeline([
            Stage("snapshot", snapshot, (), {"market_seed": 1, "revisions": [list(r) for r in revisions]}),
            Stage("universe", universe, ("snapshot",), {"top": 500, "window": 21}),
            Stage("features", features, ("snapshot", "universe")),
            Stage("cards", cards, ("snapshot", "features")),
            Stage("blend", blend, ("features", "universe"), {"weights": weights}),
            Stage("portfolio", portfolio, ("blend", "universe"), {"gross": 1.0, "rebalance": MONTH}),
            Stage("level1", level1, ("portfolio", "snapshot"), {"lag": 1, "cost": 0.0010}),
            Stage("tearsheet", tear, ("level1",), {"reps": reps, "block": MONTH}, seed),
        ], cache)
    return build


def never_in_universe(cache):
    """A listing that is never among the 500 most liquid, and a day it was listed: the target of a harmless revision."""
    out, _ = make()(cache).run(target="universe")
    uni, listed = out["universe"], out["snapshot"]["listed"]
    pid = int(np.flatnonzero(~uni.any(axis=0) & listed.any(axis=0))[0])
    return pid, int(np.flatnonzero(listed[:, pid])[5])


def always_in_universe(cache):
    out, _ = make()(cache).run(target="universe")
    pid = int(np.flatnonzero(out["universe"][YEAR:].all(axis=0))[0])
    return pid, 1000
