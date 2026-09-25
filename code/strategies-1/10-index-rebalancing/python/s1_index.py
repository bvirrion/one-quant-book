"""Index rebalancing (One Quant Book 8, chapter 10).

A 300-stock capitalisation index on firm.synthmkt (seed 1), built on day 252 and reconstituted every 126 days with a
band of 15 ranks (join at rank 285 or better, leave beyond 315): rank day, announcement 16 trading days later,
effective date 40 trading days after the rank day. Index funds track a share of each member's shares and trade the
changes at the effective date's close; the price effect of their demand is 0.7 sigma sqrt(Q / ADV), of which a share
is taken before the announcement by traders who predict the change, and half reverses over the 20 days after the
effective date (a planted path added to each stock's market-adjusted return). Measured: how well membership changes
are predicted 0, 20 and 60 days before the rank day; the returns of trading the announced changes, of predicting them,
and of providing liquidity at the effective close, for tracked shares of 5%, 15% and 30% and early shares of 0.2, 0.5
and 0.8. NumPy only.
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
for c in ("indexevent", "synthmkt"):
    sys.path.insert(0, str(FIRM / c))
from firm_indexevent import event_path, event_push, predict, reconstitute  # noqa: E402
from firm_synthmkt import simulate  # noqa: E402

SIZE, BAND, EVERY, FIRST, ANNOUNCE, EFFECTIVE, PRE, POST = 300, 15, 126, 252, 16, 40, 20, 20
COST = 0.0010


@functools.lru_cache(maxsize=1)
def market():
    P = simulate()
    R = np.where(P.listed, P.ret, np.nan)
    cap = np.where(P.listed, P.price * P.shares, np.nan)
    cprev = np.vstack([np.nan_to_num(cap[:1]), np.nan_to_num(cap[:-1])])
    mkt = np.nansum(cprev * np.nan_to_num(R), axis=1) / np.maximum(cprev.sum(axis=1), 1e-12)
    vol = np.where(P.listed, P.volume, 0.0)
    c = np.cumsum(vol, axis=0)
    adv = (c - np.vstack([np.zeros((21, vol.shape[1])), c[:-21]])) / 21
    lr = np.log1p(np.nan_to_num(R))
    c2 = np.cumsum(lr * lr, axis=0)
    sig = np.sqrt(np.maximum((c2 - np.vstack([np.zeros((63, lr.shape[1])), c2[:-63]])) / 63, 1e-8))
    ab = np.log1p(np.nan_to_num(R)) - np.log1p(mkt)[:, None]
    return P, R, cap, adv, sig, ab


@functools.lru_cache(maxsize=1)
def reconstitutions():
    """Rank days with the members before and after, additions and deletions."""
    P, R, cap, *_ = market()
    T = R.shape[0]
    members, _, _ = reconstitute(cap[FIRST], np.zeros(cap.shape[1], bool), SIZE, 0)
    out = []
    for rd in range(FIRST + EVERY, T - EFFECTIVE - POST, EVERY):
        members = members & P.listed[rd]
        new, add, drop = reconstitute(cap[rd], members, SIZE, BAND)
        out.append({"rd": rd, "before": members.copy(), "after": new, "add": add, "drop": drop})
        members = new
    return out


@functools.lru_cache(maxsize=4)
def accuracy(days: int):
    """Precision and recall of predicted additions and deletions (probability above one half), `days` before."""
    P, R, cap, adv, sig, _ = market()
    rng = np.random.default_rng(10)
    tp = fp = fn = 0
    tpd = fpd = fnd = 0
    for e in reconstitutions():
        t = e["rd"] - days
        c = np.where(P.listed[e["rd"]], cap[t], np.nan)
        p = predict(c, sig[t], e["before"], SIZE, BAND, days, 200, rng) if days > 0 else \
            reconstitute(c, e["before"], SIZE, BAND)[0].astype(float)
        pa, pd_ = (p > 0.5) & ~e["before"], (p < 0.5) & e["before"]
        tp += int((pa & e["add"]).sum())
        fp += int((pa & ~e["add"]).sum())
        fn += int((~pa & e["add"]).sum())
        tpd += int((pd_ & e["drop"]).sum())
        fpd += int((pd_ & ~e["drop"]).sum())
        fnd += int((~pd_ & e["drop"]).sum())
    return {"add_precision": tp / max(tp + fp, 1), "add_recall": tp / max(tp + fn, 1),
            "drop_precision": tpd / max(tpd + fpd, 1), "drop_recall": tpd / max(tpd + fnd, 1)}


def counts():
    ev = reconstitutions()
    return {"events": len(ev), "adds": sum(int(e["add"].sum()) for e in ev),
            "drops": sum(int(e["drop"].sum()) for e in ev)}


@functools.lru_cache(maxsize=16)
def trades(share: float = 0.15, early: float = 0.5, revert: float = 0.5):
    """Mean returns per event (additions long, deletions short, market-adjusted, planted path added): predicting
    (from 20 days before the announcement to it), trading the announcement (its close to the effective close), and
    providing liquidity at the effective close (the 20 days after); the mean push."""
    P, R, cap, adv, sig, ab = market()
    out = {"predict": [], "announce": [], "provide": [], "push": []}
    for e in reconstitutions():
        ad, ed = e["rd"] + ANNOUNCE, e["rd"] + EFFECTIVE
        for side, names in ((1, np.flatnonzero(e["add"])), (-1, np.flatnonzero(e["drop"]))):
            for i in names:
                q = share * P.shares[e["rd"], i]
                push = float(event_push(q, max(adv[e["rd"], i], 1.0), sig[e["rd"], i]))
                path = side * event_path(push, early, revert, PRE, EFFECTIVE - ANNOUNCE, POST)
                base = np.cumsum(ab[ad - PRE:ed + POST + 1, i])
                if len(base) != len(path):
                    continue
                cum = np.r_[0.0, base + path]
                a0, a1, a2 = PRE, PRE + (ed - ad), PRE + (ed - ad) + POST
                out["predict"].append(side * (cum[a0 + 1] - cum[0]))
                out["announce"].append(side * (cum[a1 + 1] - cum[a0 + 1]) - 2 * COST)
                out["provide"].append(-side * (cum[a2 + 1] - cum[a1 + 1]) - 2 * COST)
                out["push"].append(push)
    return {k: float(np.mean(v)) for k, v in out.items()} | {"n": len(out["push"]),
                                                               "se_announce": float(np.std(out["announce"]) /
                                                                                    math.sqrt(len(out["announce"])))}


def path_for_figure(share: float = 0.15, early: float = 0.5):
    """Mean planted path plus market-adjusted returns for additions, from 20 days before the announcement."""
    P, R, cap, adv, sig, ab = market()
    paths = []
    for e in reconstitutions():
        ad, ed = e["rd"] + ANNOUNCE, e["rd"] + EFFECTIVE
        for i in np.flatnonzero(e["add"]):
            push = float(event_push(share * P.shares[e["rd"], i], max(adv[e["rd"], i], 1.0), sig[e["rd"], i]))
            path = event_path(push, early, 0.5, PRE, EFFECTIVE - ANNOUNCE, POST)
            base = np.cumsum(ab[ad - PRE:ed + POST + 1, i])
            if len(base) == len(path):
                paths.append(base + path)
    return np.mean(paths, axis=0)
