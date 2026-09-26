"""One Quant Book 10, chapter 19: transaction-cost analysis of a simulated order log.

    DAYS, conditions(d)          each simulated day's volatility regime (the hidden value's jump rate) and activity
    orders(d)                    two parent orders a day (side, shares, start), decided 30 s before they start, each
                                 worked over five minutes in ten 30-second slices with a limit 8 ticks from arrival
    ALGOS                        patient: equal slices resting at the best quote (repricing, clean-up at each slice's
                                 end); urgent: an Almgren-Chriss schedule front-loaded (kT = 3), every slice crossed
    day_runs(d)                  the day without any order, with the patient algorithm, with the urgent one (the same
                                 exogenous flow): for each order and algorithm, the attribution against the decision
                                 price, the benchmarks, the reversion after the last fill, the difficulty variables
    log()                        every order worked by both algorithms (the truth), and the observed log where each
                                 order was given to one algorithm, the urgent one more often for large orders on
                                 volatile days
    study()                      what the chapter prints: benchmarks and attribution by algorithm, the pre-trade model
                                 fitted on the first half of the days and tested on the second, raw, adjusted and true
                                 differences between the algorithms, reversion, and the loop's recommendation
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("tca", "placement", "acexec", "agentmkt", "exchsim", "markout", "tcost"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_acexec import trajectory  # noqa: E402
from firm_agentmkt import SEC, T0, PopulationConfig, session  # noqa: E402
from firm_placement import Cross, Post, SliceExecutor  # noqa: E402
from firm_tca import (  # noqa: E402
    adjusted_difference,
    attribute,
    benchmarks,
    cluster_ols,
    fit_pretrade,
    peer_compare,
    pretrade,
    reversion,
)

DAYS = 100
SESSION_S = 1080.0
STARTS = (60.0, 540.0)
HORIZON, SLICES, DELAY, LIMIT = 300.0, 10, 30.0, 20
VOLS = (0.1, 0.2, 0.4)                                   # jumps of the hidden value a second
ACTS = (0.7, 1.0, 1.4)
KT = 3.0


def conditions(d: int) -> tuple:
    rng = np.random.default_rng(1900 + d)
    return VOLS[int(rng.integers(3))], ACTS[int(rng.integers(3))]


def market(vol: float, act: float) -> PopulationConfig:
    return PopulationConfig(lo_rate=3.0 * act, near=0.3, cancel=0.05, depth=10, noise=1.0 * act, fund=0.05,
                            v_rate=vol)


def orders(d: int) -> list:
    rng = np.random.default_rng(1950 + d)
    out = []
    for s in STARTS:
        qty = int(round(math.exp(rng.uniform(math.log(2000), math.log(12000))) / 100)) * 100
        out.append((1 if rng.random() < 0.5 else -1, qty, s))
    return out


def _slices(d: int, urgent: bool, arrivals) -> list:
    sl = []
    for (side, qty, start), a in zip(orders(d), arrivals, strict=True):
        if urgent:
            x = trajectory(qty, 1.0, KT, np.linspace(0, 1, SLICES + 1))
            q = np.round(-np.diff(x) / 100) * 100
        else:
            q = np.full(SLICES, round(qty / SLICES / 100) * 100)
        q[-1] += qty - q.sum()
        lim = None
        if a is not None:                                      # on the tick grid, LIMIT ticks away from arrival
            lim = (math.floor(a / 100) + LIMIT) * 100 if side > 0 else (math.ceil(a / 100) - LIMIT) * 100
        for k in range(SLICES):
            t = T0 + int((start + k * HORIZON / SLICES) * SEC)
            if q[k] > 0:
                sl.append((t, "B" if side > 0 else "S", int(q[k]), HORIZON / SLICES,
                           None if lim is None else int(lim)))
    return sl


def _mid(res):
    top = res.tape().top
    ok = (top["bid"] > 0) & (top["ask"] > 0)
    return top["t"][ok], 0.5 * (top["bid"][ok] + top["ask"][ok])


def _at(path, t):
    i = np.searchsorted(path[0], t, side="right") - 1
    return float(path[1][max(i, 0)])


@functools.cache
def day_runs(d: int) -> list:
    vol, act = conditions(d)
    cfg = market(vol, act)
    seed = 19_000 + d
    base, _ = session(cfg, SESSION_S, seed)
    cf = _mid(base)
    cf_tr = base.tape().trades
    arrivals = [_at(cf, s) * 100 for _, _, s in orders(d)]                  # simulator units, for the limit
    rows = []
    for urgent in (False, True):
        ex = SliceExecutor(_slices(d, urgent, arrivals), Cross() if urgent else Post(0, True), check_s=1.0)
        res, _ = session(cfg, SESSION_S, seed, agents=[ex])
        mid = _mid(res)
        tr = res.tape().trades
        fl = res.agents["placer"].fills
        close = float(mid[1][-1])
        for j, (side, qty, start) in enumerate(orders(d)):
            t0, t1 = start, start + HORIZON + HORIZON / SLICES
            f = [x for x in fl if t0 <= (x[0] - T0) / SEC < t1]
            ft = np.array([(x[0] - T0) / SEC for x in f])
            fp = np.array([x[4] / 100.0 for x in f])
            fq = np.array([x[5] for x in f], float)
            fee = np.array([x[7] / 1e6 / x[5] / 0.01 for x in f])            # ticks a share
            dec, arr, end = _at(mid, start - DELAY), _at(mid, start), _at(mid, t1)
            at = attribute(side, qty, dec, arr, np.c_[ft, fp, fq, fee], mid, cf, end, start)
            win = (tr["t"] >= t0) & (tr["t"] < t1)
            bm = benchmarks(side, np.c_[fp, fq], arr, np.c_[tr["price"][win], tr["qty"][win]],
                            np.c_[tr["price"], tr["qty"]], close) if fq.sum() > 0 else None
            cwin = (cf_tr["t"] >= t0) & (cf_tr["t"] < t1)
            vol_w = float(cf_tr["qty"][cwin].sum())
            rows.append({"day": d, "order": j, "urgent": urgent, "side": side, "qty": qty, "vol": vol, "act": act,
                         "part": qty / vol_w, "move": _at(cf, t1) - _at(cf, t0),
                         "attr": at, "bench": bm, "t_end": float(ft.max()) if len(ft) else t1,
                         "rev": reversion(side, float(ft.max()) if len(ft) else t1, mid, (30.0, 120.0)),
                         "cost": at["total"]})
    return rows


@functools.cache
def log(days: int = DAYS) -> list:
    return [r for d in range(days) for r in day_runs(d)]


def assigned(r: dict) -> bool:
    """The desk's routing: the urgent algorithm gets more large or volatile orders."""
    z = (math.log(r["qty"]) - math.log(5000)) / 0.5
    p = 1 / (1 + math.exp(-(-0.5 + 1.5 * z + 1.5 * (r["vol"] == VOLS[-1]))))
    return bool(np.random.default_rng(7_000 + 10 * r["day"] + r["order"]).random() < p)


def _sigma_regime(rows) -> dict:
    """The desk's pre-trade volatility for each regime: the standard deviation of the mid's move over an order's
    window on the days without orders, pooled over the log."""
    return {v: float(np.std([r["move"] for r in rows if r["vol"] == v and not r["urgent"]], ddof=1)) for v in VOLS}


@functools.cache
def study(days: int = DAYS) -> dict:
    rows = log(days)
    sig = _sigma_regime(rows)
    pat = [r for r in rows if not r["urgent"]]
    urg = [r for r in rows if r["urgent"]]
    out = {"n_orders": len(pat), "sigma": sig}
    # benchmarks and attribution, every order under both algorithms
    for name, rs in (("patient", pat), ("urgent", urg)):
        out[name] = {k: float(np.mean([r["attr"][k] for r in rs]))
                     for k in ("delay", "spread", "impact", "timing", "opportunity", "fees", "total", "filled")}
        out[name]["bench"] = {k: float(np.mean([r["bench"][k] for r in rs if r["bench"]]))
                              for k in ("arrival", "interval_vwap", "day_vwap", "close")}
        out[name]["rev"] = np.mean([r["rev"] for r in rs], axis=0)
        out[name]["check"] = float(max(abs(r["attr"]["check"]) for r in rs))
        out[name]["sd"] = float(np.std([r["cost"] for r in rs], ddof=1))
    # the truth: every order under both algorithms, paired
    diff = np.array([u["cost"] - p["cost"] for p, u in zip(pat, urg, strict=True)])
    days_ = np.array([p["day"] for p in pat])
    b, v = cluster_ols(diff, np.ones((len(diff), 1)), days_)
    out["true"] = (float(b[0]), float(math.sqrt(v[0, 0])))
    # the observed log: one algorithm per order
    obs = [u if assigned(p) else p for p, u in zip(pat, urg, strict=True)]
    y = np.array([r["cost"] for r in obs])
    treat = np.array([float(r["urgent"]) for r in obs])
    s = np.array([sig[r["vol"]] for r in obs])
    part = np.array([r["part"] for r in obs])
    diffic = s * np.sqrt(part)
    ctrl = np.c_[s, part, diffic, treat * (diffic - diffic.mean())]
    out["share_urgent"] = float(treat.mean())
    out["urgent_big"] = (float(np.mean([r["qty"] for r in obs if r["urgent"]])),
                         float(np.mean([r["qty"] for r in obs if not r["urgent"]])))
    out["diff"] = adjusted_difference(y, treat, ctrl, days_)
    out["diff_part"] = adjusted_difference(y, treat, part[:, None], days_)          # participation only
    # pre-trade model on the first half (patient orders, execution cost per filled share), tested on the second
    half = days // 2
    tr = [r for r in pat if r["day"] < half and r["bench"]]
    te = [r for r in pat if r["day"] >= half and r["bench"]]
    fit = fit_pretrade([r["bench"]["arrival"] for r in tr], [sig[r["vol"]] for r in tr], [r["part"] for r in tr],
                       np.full(len(tr), -0.5))
    pred = pretrade(-0.5, fit["eta_fixed"], [sig[r["vol"]] for r in te], [r["part"] for r in te])
    real = np.array([r["bench"]["arrival"] for r in te])
    out["pretrade"] = {"eta": fit["eta_fixed"], "se": fit["se_eta"], "pred": float(np.mean(pred)),
                       "real": float(real.mean()), "real_se": float(real.std(ddof=1) / math.sqrt(len(real))),
                       "corr": float(np.corrcoef(pred, real)[0, 1]), "n_train": len(tr), "n_test": len(te)}
    order = np.argsort(pred)
    out["calibration"] = [(float(pred[g].mean()), float(real[g].mean()), float(real[g].std(ddof=1) / math.sqrt(len(g))))
                          for g in np.array_split(order, 5)]
    # peer comparison: each algorithm's cost against the pre-trade prediction, on the observed log
    pred_all = pretrade(-0.5, fit["eta_fixed"], s, part)
    out["peer"] = peer_compare(y, pred_all, np.where(treat > 0, "urgent", "patient"), days_)
    # closing the loop: fit cost on algorithm x difficulty (first half of the observed log), route the second half by
    # the lower prediction, score with the truth
    first = days_ < half
    xx = np.c_[np.ones(len(y)), treat, s, s * np.sqrt(part), treat * s * np.sqrt(part)]
    beta, _ = cluster_ols(y[first], xx[first], days_[first])
    x0 = np.c_[np.ones(len(y)), np.zeros(len(y)), s, s * np.sqrt(part), np.zeros(len(y))]
    x1 = np.c_[np.ones(len(y)), np.ones(len(y)), s, s * np.sqrt(part), s * np.sqrt(part)]
    pick = (x1 @ beta < x0 @ beta)[~first]
    cp = np.array([r["cost"] for r in pat])[~first]
    cu = np.array([r["cost"] for r in urg])[~first]
    out["loop"] = {"patient": float(cp.mean()), "urgent": float(cu.mean()), "observed": float(y[~first].mean()),
                   "model": float(np.where(pick, cu, cp).mean()), "share_urgent": float(pick.mean()),
                   "beta": beta.tolist()}
    return out
