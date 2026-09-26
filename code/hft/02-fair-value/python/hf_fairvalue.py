"""Fair value (One Quant Book 11, chapter 2).

Synthetic: three firm.tape markets on one efficient price. A leads (an index future); B follows A's efficient price
LAG seconds later (the ETF on the index, on its main venue); C is B on a second venue (same efficient price as B,
independent order flow). The chapter's estimators of B's fair price are scored on a 0.1-second grid of the second
simulated hour against B's efficient price (the truth, never seen by a trader) and as forecasts of B's mid FWD seconds
later. Every parameter (the filter's q and r, the microprice table) is fitted on the first hour only.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys
from dataclasses import replace

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
for dep in ("fairprice", "tape", "markout"):
    sys.path.insert(0, str(ROOT / "firm" / dep))
import firm_fairprice as fp  # noqa: E402
import firm_tape as ft  # noqa: E402
from firm_markout import ref_at  # noqa: E402

LAG = 0.5            # seconds by which B's efficient price follows A's
FWD = 5.0            # forecast horizon (seconds)
STEP = 0.1           # evaluation grid
CFG = replace(ft.TapeConfig(), seconds=3600.0, news_at=None, seed=31)


@functools.cache
def markets(lag: float = LAG, seed: int = 31):
    cfg = replace(CFG, seed=seed)
    rng = np.random.default_rng(cfg.seed + 1000)
    act = ft.activity(cfg, rng)
    vt, v = ft.efficient_path(cfg, rng, act)
    a = ft.simulate(cfg, (vt, v, act))
    shifted = np.concatenate([[0.0], np.minimum(vt[1:] + lag, cfg.seconds)])
    b = ft.simulate(replace(cfg, seed=seed + 11), (shifted, v, act))
    c = ft.simulate(replace(cfg, seed=seed + 23), (shifted, v, act))
    return a, b, c, (shifted, v)


def _tops(tape):
    top = tape.top[tape.n_open - 1:]
    return top["t"].astype(float), top


def _obs(tape, kind: str, g=None):
    """(times, values) of a tape's mid, weighted mid or microprice after every event."""
    t, top = _tops(tape)
    if kind == "mid":
        y = 0.5 * (top["bid"] + top["ask"])
    elif kind == "wmid":
        y = fp.weighted_mid(top["bid"], top["bid_qty"], top["ask"], top["ask_qty"])
    else:
        y = fp.micro(top["bid"], top["bid_qty"], top["ask"], top["ask_qty"], g)
    return t, np.asarray(y, float)


def grid(first: bool) -> np.ndarray:
    T = CFG.seconds
    lo, hi = (60.0, T / 2 - FWD) if first else (T / 2, T - FWD)
    return np.arange(lo, hi, STEP)


@functools.cache
def fitted(lag: float = LAG, seed: int = 31):
    """Microprice tables for B and C and the filter's q and r, fitted on the first hour."""
    a, b, c, (vt, v) = markets(lag, seed)
    tg = grid(True)
    gs = []
    for tape in (b, c):
        t, top = _tops(tape)
        i = np.searchsorted(t, tg, side="right") - 1
        mid = 0.5 * (top["bid"] + top["ask"])
        dmid = ref_at(t, mid, tg + FWD) - mid[i]
        gs.append(fp.fit_micro(fp.imbalance(top["bid_qty"][i], top["ask_qty"][i]), (top["ask"] - top["bid"])[i],
                               dmid, 5))
    jumps = np.diff(v)[(vt[1:] < CFG.seconds / 2)]
    q = float((jumps**2).sum() / (CFG.seconds / 2))
    target = ref_at(*_obs(b, "mid"), tg + FWD)            # the future mid: observable, no truth needed
    srcs = [_obs(b, "micro", gs[0]), _obs(c, "micro", gs[1]), _obs(a, "mid")]
    r = [float(np.var(ref_at(t, y, tg) - target)) for t, y in srcs]
    return gs, q, r


def _levels(lag: float, seed: int, first: bool):
    a, b, c, (vt, v) = markets(lag, seed)
    gs, _, _ = fitted(lag, seed)
    tg = grid(first)
    lv = {"mid": ref_at(*_obs(b, "mid"), tg), "wmid": ref_at(*_obs(b, "wmid"), tg),
          "micro": ref_at(*_obs(b, "micro", gs[0]), tg), "c_micro": ref_at(*_obs(c, "micro", gs[1]), tg),
          "a_mid": ref_at(*_obs(a, "mid"), tg)}
    return tg, lv, ref_at(vt, v, tg), ref_at(*_obs(b, "mid"), tg + FWD)


def _design(lv: dict, kind: str) -> np.ndarray:
    base = lv["mid"]
    cols = {"consolidated": [lv["micro"] - base, lv["c_micro"] - base],
            "cross": [lv["micro"] - base, lv["c_micro"] - base, lv["a_mid"] - base]}[kind]
    return np.column_stack(cols)


@functools.cache
def weights(lag: float = LAG, seed: int = 31) -> dict:
    """Least-squares weights of the regression fair prices, fitted on the first hour: future mid minus mid on the
    gaps between each source and the mid."""
    _, lv, _, fut = _levels(lag, seed, True)
    return {k: np.linalg.lstsq(_design(lv, k), fut - lv["mid"], rcond=None)[0] for k in ("consolidated", "cross")}


def estimates(lag: float = LAG, seed: int = 31) -> dict:
    """Every estimator of B's fair price on the second-hour grid."""
    a, b, c, _ = markets(lag, seed)
    gs, q, r = fitted(lag, seed)
    tg, lv, _, _ = _levels(lag, seed, False)
    w = weights(lag, seed)
    out = {"mid": lv["mid"], "wmid": lv["wmid"], "micro": lv["micro"]}
    for k in ("consolidated", "cross"):
        out[k] = lv["mid"] + _design(lv, k) @ w[k]
    for name, srcs in (("consolidated_filter", [_obs(b, "micro", gs[0]), _obs(c, "micro", gs[1])]),
                       ("cross_filter", [_obs(b, "micro", gs[0]), _obs(c, "micro", gs[1]), _obs(a, "mid")])):
        tt = np.concatenate([s[0] for s in srcs])
        ss = np.concatenate([np.full(len(s[0]), k) for k, s in enumerate(srcs)])
        yy = np.concatenate([s[1] for s in srcs])
        o = np.argsort(tt, kind="stable")
        est = fp.run_filter(tt[o], ss[o], yy[o], q, [r[k] for k in range(len(srcs))])
        out[name] = ref_at(tt[o], est, tg)
    return out


NAMES = ("mid", "wmid", "micro", "consolidated", "consolidated_filter", "cross", "cross_filter")
SEEDS = (31, 32, 33)


def scores(lag: float = LAG, seed: int = 31) -> dict:
    """RMSE (ticks) against B's efficient price now, and against B's mid FWD seconds later."""
    _, _, truth, future = _levels(lag, seed, False)
    e = estimates(lag, seed)
    return {k: (fp.rmse(e[k], truth), fp.rmse(e[k], future)) for k in NAMES}


def table(lag: float = LAG) -> dict:
    """Mean over SEEDS of each estimator's RMSE and of its RMSE relative to the mid's (percent)."""
    rows = [scores(lag, s) for s in SEEDS]
    out = {}
    for k in NAMES:
        tr = np.mean([r[k][0] for r in rows])
        fu = np.mean([r[k][1] for r in rows])
        rel_t = np.mean([100 * (r[k][0] / r["mid"][0] - 1) for r in rows])
        rel_f = np.mean([100 * (r[k][1] / r["mid"][1] - 1) for r in rows])
        out[k] = {"truth": float(tr), "future": float(fu), "rel_truth": float(rel_t), "rel_future": float(rel_f)}
    return out


LAGS = (0.1, 0.25, 0.5, 1.0, 2.0)


def by_lag(names=("micro", "consolidated", "cross", "cross_filter")) -> dict:
    """RMSE against the future mid relative to the mid's (percent), mean over SEEDS, for each lead of A over B."""
    return {lag: {k: table(lag)[k]["rel_future"] for k in names} for lag in LAGS}


def window(lag: float = 2.0, seed: int = 31, before: float = 5.0, after: float = 15.0) -> dict:
    """B's efficient price, mid and cross-instrument fair price around the largest ten-second move of B's efficient
    price in the second hour."""
    vt, v = markets(lag, seed)[3]
    tg, lv, truth, _ = _levels(lag, seed, False)
    e = estimates(lag, seed)
    move = ref_at(vt, v, tg + 10.0) - truth
    i = int(np.argmax(np.abs(move)))
    sel = (tg >= tg[i] - before) & (tg <= tg[i] + after)
    return {"t": tg[sel] - tg[i], "truth": truth[sel], "mid": lv["mid"][sel], "cross": e["cross"][sel]}
