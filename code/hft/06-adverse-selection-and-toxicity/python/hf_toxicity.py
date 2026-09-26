"""Adverse selection and toxicity (One Quant Book 11, chapter 6).

On firm.tape through firm.mmharness: a one-lot market maker at the others' best prices (at most five lots). (1) The
mark-outs of its fills by the class of the trader on the other side (informed or not: the simulator's truth, never
seen by the quoter) and by period (before, during and after a news window). (2) A toxicity score fitted on
calibration sessions: ordinary least squares of each fill's ten-second mark-out on four features observable when the
quote rests (firm.toxicity.FlowTracker). (3) On other sessions, the same quoter fading or widening the side whose
score is above zero (expected mark-out below zero), against the base quoter.
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
for dep in ("mmharness", "toxicity", "tape"):
    sys.path.insert(0, str(ROOT / "firm" / dep))
import firm_mmharness as mh  # noqa: E402
import firm_tape as ft  # noqa: E402
import firm_toxicity as tx  # noqa: E402

SESSION = 1200.0
NEWS = (600.0, 90.0)                  # a news window in the middle of each session
CAL_SEEDS = (81, 82, 83, 84, 85, 86)
TEST_SEEDS = (91, 92, 93, 94, 95, 96)
H = 10.0


def cfg(seed: int) -> ft.TapeConfig:
    return replace(ft.TapeConfig(), seed=seed, seconds=SESSION, news_at=NEWS[0], news_len=NEWS[1])


@functools.cache
def run(seed: int, mode: str = "base", threshold: float = 0.0, restore: float | None = None) -> tuple:
    model = fitted() if mode != "base" else None
    q = tx.ToxicQuoter(model, mode, threshold, record=True, restore=restore)
    r = mh.run_tape(q, cfg(seed))
    return r, np.array(q.at_fill)


def _markouts(r: mh.Result) -> np.ndarray:
    return r.markouts([H])[:, 0]


def by_class(seeds=CAL_SEEDS) -> dict:
    """Ten-second mark-out (ticks a share) of the base quoter's fills by the aggressor's class, and the informed
    share of fills."""
    mo, inf, qty = [], [], []
    for s in seeds:
        r, _ = run(s)
        mo.append(_markouts(r))
        inf.append(r.extra["informed"])
        qty.append(r.fills["qty"])
    mo, inf, qty = np.concatenate(mo), np.concatenate(inf), np.concatenate(qty)
    g = tx.grouped(mo[:, None], qty, np.where(inf, "informed", "uninformed"))
    return {"informed": g["informed"][0][0], "uninformed": g["uninformed"][0][0], "se_informed": g["informed"][1][0],
            "se_uninformed": g["uninformed"][1][0], "share_informed": float(qty[inf].sum() / qty.sum()),
            "all": float(qty @ mo / qty.sum()), "fills": int(len(mo))}


def by_period(seeds=CAL_SEEDS) -> dict:
    """Ten-second mark-out and informed share of fills before, during and after the news window."""
    out = {}
    lo, hi = NEWS[0], NEWS[0] + NEWS[1]
    for name, sel in (("before", lambda t: t < lo), ("during", lambda t: (t >= lo) & (t < hi)),
                      ("after", lambda t: t >= hi)):
        mo, inf, qty = [], [], []
        for s in seeds:
            r, _ = run(s)
            k = sel(r.fills["t"])
            mo.append(_markouts(r)[k])
            inf.append(r.extra["informed"][k])
            qty.append(r.fills["qty"][k])
        mo, inf, qty = np.concatenate(mo), np.concatenate(inf), np.concatenate(qty)
        length = {"before": lo, "during": hi - lo, "after": SESSION - hi}[name]
        out[name] = {"markout": float(qty @ mo / qty.sum()), "informed": float(qty[inf].sum() / qty.sum()),
                     "fills_per_min": float(len(mo) / len(seeds) / (length / 60))}
    return out


@functools.cache
def fitted() -> tx.ToxicityModel:
    X, y = _training()
    return tx.ToxicityModel.fit(X, y)


def _training():
    X, y = [], []
    for s in CAL_SEEDS:
        r, af = run(s)
        mo = _markouts(r)
        # at_fill rows follow the fills that had features recorded; align on fill times and sides
        rows = {(round(a[0], 9), int(a[1])): a[2:] for a in af}
        for t, side, m in zip(r.fills["t"], r.fills["side"], mo, strict=True):
            f = rows.get((round(float(t), 9), int(side)))
            if f is not None:
                X.append(f)
                y.append(m)
    return np.array(X), np.array(y)


def fit_quality() -> dict:
    """In-sample and out-of-sample correlation of the score's forecast with realised mark-outs."""
    X, y = _training()
    m = fitted()
    Xt, yt = _test_rows()
    return {"coef": m.coef, "n": len(y), "corr_in": float(np.corrcoef(m.predict(X), y)[0, 1]),
            "corr_out": float(np.corrcoef(m.predict(Xt), yt)[0, 1]), "n_out": len(yt)}


MODES = ("base", "fade", "widen")


def responses() -> dict:
    """On the test sessions: shares, ten-second mark-out per share, ten-second edge a session ($), informed share of
    fills and P&L, for each response."""
    out = {}
    for mode in MODES:
        rs = [run(s, mode)[0] for s in TEST_SEEDS]
        vol = sum(r.volume() for r in rs)
        mo = sum(float(_markouts(r) @ r.fills["qty"]) for r in rs)
        inf = sum(float(r.fills["qty"][r.extra["informed"]].sum()) for r in rs)
        pnl = [r.pnl() for r in rs]
        per = np.concatenate([_markouts(r) for r in rs])
        out[mode] = {"shares": vol / len(rs), "markout": mo / vol, "edge": mo / len(rs) * 0.01,
                     "se": float(per.std(ddof=1) / np.sqrt(len(per))),
                     "informed": inf / vol, "pnl": float(np.mean(pnl)), "sd": float(np.std(pnl, ddof=1)),
                     "messages": float(np.mean([r.messages for r in rs]))}
    return out


def _test_rows():
    Xt, yt = [], []
    for s in TEST_SEEDS:
        r, af = run(s)
        mo = _markouts(r)
        rows = {(round(a[0], 9), int(a[1])): a[2:] for a in af}
        for t, side, v in zip(r.fills["t"], r.fills["side"], mo, strict=True):
            f = rows.get((round(float(t), 9), int(side)))
            if f is not None:
                Xt.append(f)
                yt.append(v)
    return np.array(Xt), np.array(yt)


def calibration(n: int = 5) -> dict:
    """Out of sample: the base quoter's test-session fills sorted into n groups by predicted mark-out; mean predicted
    and realised ten-second mark-out per group (ticks a share)."""
    X, y = _test_rows()
    p = fitted().predict(X)
    edges = np.quantile(p, np.linspace(0, 1, n + 1))
    g = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, n - 1)
    return {"pred": np.array([p[g == k].mean() for k in range(n)]),
            "real": np.array([y[g == k].mean() for k in range(n)]),
            "se": np.array([y[g == k].std(ddof=1) / np.sqrt((g == k).sum()) for k in range(n)])}


THRESHOLDS = (0.0, 0.2, 0.4, 0.6)


def fade_sweep() -> dict:
    """Fading at several score thresholds, on the test sessions."""
    out = {}
    for th in THRESHOLDS:
        rs = [run(s, "fade", th)[0] for s in TEST_SEEDS]
        vol = sum(r.volume() for r in rs)
        mo = sum(float(_markouts(r) @ r.fills["qty"]) for r in rs)
        per = np.concatenate([_markouts(r) for r in rs])
        inf = sum(float(r.fills["qty"][r.extra["informed"]].sum()) for r in rs)
        out[th] = {"shares": vol / len(rs), "markout": mo / vol, "edge": mo / len(rs) * 0.01,
                   "se": float(per.std(ddof=1) / np.sqrt(len(per))), "informed": inf / vol,
                   "messages": float(np.mean([r.messages for r in rs]))}
    return out


def hysteresis(threshold: float = 0.2, restore: float = 0.0) -> dict:
    """Fade above `threshold`, restore below `restore`, on the test sessions."""
    rs = [run(s, "fade", threshold, restore)[0] for s in TEST_SEEDS]
    vol = sum(r.volume() for r in rs)
    mo = sum(float(_markouts(r) @ r.fills["qty"]) for r in rs)
    inf = sum(float(r.fills["qty"][r.extra["informed"]].sum()) for r in rs)
    return {"shares": vol / len(rs), "markout": mo / vol, "informed": inf / vol,
            "messages": float(np.mean([r.messages for r in rs]))}
