"""Short-horizon alpha (One Quant Book 11, chapter 7).

Two firm.tape markets on one efficient price: A leads (the index future), B follows LAG seconds later (the fund). The
market maker quotes B and reads A's book. (1) Features of B's book and trades and of A's recent move, after every
message of B, and the mid change of B over the next HORIZON seconds, on calibration sessions (no market maker): the
information coefficient of each feature and of their ridge combination, by horizon, out of sample. (2) The forecast
coupled to a one-lot quoter on B (firm.mmharness): base, forecast skew, skew plus a take threshold, and the same with
the forecast one message late.
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
for dep in ("mmharness", "hfalpha", "tape"):
    sys.path.insert(0, str(ROOT / "firm" / dep))
import firm_hfalpha as al  # noqa: E402
import firm_mmharness as mh  # noqa: E402
import firm_tape as ft  # noqa: E402

LAG = 0.5
WINDOW = 1.0
HORIZON = 2.0
SESSION = 1200.0
CAL_SEEDS = (101, 102, 103, 104)
VAL_SEEDS = (105, 106)
TEST_SEEDS = (111, 112, 113, 114, 115, 116)
HORIZONS = (0.5, 1.0, 2.0, 5.0, 10.0)


def cfg(seed: int) -> ft.TapeConfig:
    return replace(ft.TapeConfig(), seed=seed, seconds=SESSION, news_at=None)


@functools.cache
def pair(seed: int):
    """A's tape, B's efficient-price path (A's, LAG seconds later) and B's tape without a market maker."""
    c = cfg(seed)
    rng = np.random.default_rng(c.seed + 1000)
    act = ft.activity(c, rng)
    vt, v = ft.efficient_path(c, rng, act)
    a = ft.simulate(c, (vt, v, act))
    shifted = np.concatenate([[0.0], np.minimum(vt[1:] + LAG, c.seconds)])
    bpath = (shifted, v, act)
    b = ft.simulate(replace(c, seed=seed + 11), bpath)
    return a, bpath, b


def leader(a) -> tuple[np.ndarray, np.ndarray]:
    top = a.top[a.n_open - 1:]
    return top["t"].astype(float), 0.5 * (top["bid"] + top["ask"]).astype(float)


@functools.cache
def data(seed: int):
    a, _, b = pair(seed)
    t, X, mid = al.stream(b, WINDOW, leader(a))
    return t, X, mid


def xy(seeds, horizon: float = HORIZON):
    Xs, ys = [], []
    for s in seeds:
        t, X, mid = data(s)
        Xs.append(X)
        ys.append(al.target(t, mid, horizon))
    return np.vstack(Xs), np.concatenate(ys)


@functools.cache
def model(horizon: float = HORIZON) -> al.Ridge:
    X, y = xy(CAL_SEEDS, horizon)
    return al.Ridge.fit(X, y, lam=1.0)


def ics(horizon: float = HORIZON) -> dict:
    """Out-of-sample (validation sessions) information coefficient of each feature (sign as fitted) and of the
    combination, forecasting B's mid change over `horizon`."""
    X, y = xy(VAL_SEEDS, horizon)
    m = model(horizon)
    out = {f: al.ic(np.sign(m.coef[i]) * X[:, i], y) for i, f in enumerate(al.FEATURES)}
    out["combined"] = al.ic(m.predict(X), y)
    return out


def ic_by_horizon() -> dict:
    return {h: ics(h) for h in HORIZONS}


def coef_per_unit(horizon: float = HORIZON) -> dict:
    m = model(horizon)
    return {f: float(m.coef[i] / m.scale[i]) for i, f in enumerate(al.FEATURES)}


# --- coupling the forecast to quoting ---------------------------------------------------------------------------
SKEW = 0.3           # ticks: withdraw the side against a forecast beyond this
TAKE = 0.9           # ticks: half the spread (0.5) plus the taker fee (0.1 of a tick here) plus a margin
FEES = mh.Fees(make=0.0, take=0.001)
POLICIES = {"base": (None, None, 0), "skew": (SKEW, None, 0), "skew + take": (SKEW, TAKE, 0),
            "skew + take, one message late": (SKEW, TAKE, 1)}


@functools.cache
def run(policy: str, seed: int) -> tuple:
    skew, take, lag = POLICIES[policy]
    a, bpath, _ = pair(seed)
    q = al.AlphaQuoter(model() if policy != "base" else None, WINDOW, leader(a), skew, take, lag)
    r = mh.run_tape(q, replace(cfg(seed), seed=seed + 11), fees=FEES, v_path=bpath)
    return r, q.takes


def compare() -> dict:
    out = {}
    for p in POLICIES:
        rows = [run(p, s) for s in TEST_SEEDS]
        rs = [x[0] for x in rows]
        f = np.concatenate([r.fills for r in rs])
        mo = np.concatenate([r.markouts([HORIZON])[:, 0] for r in rs])
        pas = f["passive"]
        pnl = [r.pnl() for r in rs]
        out[p] = {"pnl": float(np.mean(pnl)), "sd": float(np.std(pnl, ddof=1)),
                  "passive_shares": float(f["qty"][pas].sum() / len(rs)),
                  "passive_markout": float(mo[pas] @ f["qty"][pas] / f["qty"][pas].sum()),
                  "takes": float(np.mean([x[1] for x in rows])),
                  "take_markout": float(mo[~pas] @ f["qty"][~pas] / f["qty"][~pas].sum()) if (~pas).any() else 0.0,
                  "messages": float(np.mean([r.messages for r in rs]))}
    return out


def calibration(n: int = 10) -> dict:
    """Validation sessions: forecasts sorted into n groups; mean forecast and mean realised change (ticks)."""
    X, y = xy(VAL_SEEDS)
    p = model().predict(X)
    ok = np.isfinite(y)
    p, y = p[ok], y[ok]
    edges = np.quantile(p, np.linspace(0, 1, n + 1))
    g = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, n - 1)
    return {"pred": np.array([p[g == k].mean() for k in range(n)]),
            "real": np.array([y[g == k].mean() for k in range(n)]),
            "share_beyond_take": float(np.mean(np.abs(p) > TAKE)),
            "share_beyond_skew": float(np.mean(np.abs(p) > SKEW))}


DELAYS = (0, 1, 2, 5, 10, 20, 50)


def ic_by_delay() -> dict:
    """Validation sessions: IC of the forecast made from the features k messages old, against B's mid change over the
    next HORIZON seconds from now; and the median time those k messages take."""
    m = model()
    out = {}
    for k in DELAYS:
        ps, ys, dts = [], [], []
        for s in VAL_SEEDS:
            t, X, mid = data(s)
            y = al.target(t, mid, HORIZON)
            p = m.predict(X)
            if k:
                p, y, dt = p[:-k], y[k:], t[k:] - t[:-k]
            else:
                dt = np.zeros(len(t))
            ps.append(p)
            ys.append(y)
            dts.append(dt)
        out[k] = {"ic": al.ic(np.concatenate(ps), np.concatenate(ys)),
                  "ms": float(1e3 * np.median(np.concatenate(dts)))}
    return out
