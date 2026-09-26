"""firm.qreactive -- queue-reactive models of the best queues (One Quant Book 11, chapter 5).

The queue-reactive model of Huang, Lehalle and Rosenbaum treats each best queue as a birth-death process whose rates
depend on the queue's current size: limit orders join the back at lam_L(q), cancellations remove orders at lam_C(q),
market orders remove orders from the front at lam_M(q). When a queue empties the price moves by one tick and new
queues are drawn from a regeneration distribution. Sizes are in lots here (one event = one lot).

This module (i) estimates the intensities of the best bid and ask queues, pooled over the two sides, from an
order-by-order message stream (firm.tape's msgs and top, or firm.exchsim's res.tape()); (ii) simulates the model with
one of the market maker's own orders in the bid queue, many paths at once, and returns the value of that place in the
queue: the probability of a fill before the other side's queue empties or a time limit, and the expected P&L of the
order marked at the mid H seconds after its fill, in ticks per share. Book 10 ch. 6 defines the queue value; this is
how a market maker computes it and turns it into rules to join a queue and to leave it.

API (stable):
    estimate(msgs, top, lot, qmax, n_open)          {'q': 0..qmax, 'L', 'C', 'M' (lots per second by queue size),
                                                    'time' (seconds spent at each size), 'regen' (probabilities of the
                                                    size of a new best queue after a price change)}
    QRModel(L, C, M, regen)                         intensities indexed by queue size (lots), capped at the last entry
    order_value(model, ahead, same, opp, H, tmax, paths, seed)
                                                    arrays (broadcast) of the state; returns {'fill', 'value',
                                                    'adverse'}:
                                                    fill probability, expected P&L per share of the order (ticks),
                                                    expected mid move against the order H seconds after a fill
    value_table(model, qs, H, tmax, paths, seed)    value of the back of the queue (ahead = same) and of the front
                                                    (ahead = 0) for every (same, opp) in qs x qs
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def estimate(msgs, top, lot: int = 100, qmax: int = 30, n_open: int = 0) -> dict:
    """Event rates at the best bid and ask by the queue's size (lots) before the event, pooled over sides."""
    t = msgs["t"].astype(float)
    kinds, sides, prices, qtys = msgs["kind"], msgs["side"].astype(int), msgs["price"], msgs["qty"]
    L, C, M = np.zeros(qmax + 1), np.zeros(qmax + 1), np.zeros(qmax + 1)
    T = np.zeros(qmax + 1)
    regen = np.zeros(qmax + 1)
    for i in range(max(n_open, 1), len(msgs)):
        prev = top[i - 1]
        dt = t[i] - t[i - 1]
        for side, px, qq in ((1, prev["bid"], prev["bid_qty"]), (-1, prev["ask"], prev["ask_qty"])):
            s = min(int(round(qq / lot)), qmax)
            T[s] += dt
            if sides[i] == side and prices[i] == px:
                n = qtys[i] / lot
                if kinds[i] == b"A":
                    L[s] += n
                elif kinds[i] == b"X":
                    C[s] += n
                else:
                    M[s] += n
        cur = top[i]
        for p0, p1, q1 in ((prev["bid"], cur["bid"], cur["bid_qty"]), (prev["ask"], cur["ask"], cur["ask_qty"])):
            if p1 != p0:
                regen[min(int(round(q1 / lot)), qmax)] += 1
    with np.errstate(invalid="ignore", divide="ignore"):
        out = {"q": np.arange(qmax + 1), "L": np.where(T > 0, L / T, 0.0), "C": np.where(T > 0, C / T, 0.0),
               "M": np.where(T > 0, M / T, 0.0), "time": T}
    out["regen"] = regen / regen.sum() if regen.sum() else np.full(qmax + 1, 1.0 / (qmax + 1))
    return out


@dataclass(frozen=True)
class QRModel:
    L: np.ndarray
    C: np.ndarray
    M: np.ndarray
    regen: np.ndarray

    def rates(self, q):
        j = np.clip(np.asarray(q, int), 0, len(self.L) - 1)
        return self.L[j], np.where(np.asarray(q) > 0, self.C[j], 0.0), np.where(np.asarray(q) > 0, self.M[j], 0.0)


def order_value(model: QRModel, ahead, same, opp, H: float = 10.0, tmax: float = 60.0, paths: int = 2000,
                seed: int = 1) -> dict:
    """One lot of ours sits in the bid queue with `ahead` lots in front of it; the bid queue holds `same` lots in all
    (ours included) and the ask queue `opp`. Market sells take the bid queue from the front; cancellations hit the
    other orders at random; limit orders join the back. The order is filled when a market sell reaches it; it is
    abandoned (value 0) if the ask queue empties first (the price moves away) or after tmax. After a fill the mid is
    followed for H seconds, with each emptied queue moving it one tick and both queues redrawn from `regen`; the
    order's P&L is 0.5 tick plus the mid's move, per share."""
    ahead, same, opp = np.broadcast_arrays(np.asarray(ahead, int), np.asarray(same, int), np.asarray(opp, int))
    shape = ahead.shape
    ahead = np.repeat(ahead.ravel(), paths)
    same = np.repeat(same.ravel(), paths)
    opp = np.repeat(opp.ravel(), paths)
    rng = np.random.default_rng(seed)
    n = len(ahead)
    behind = same - ahead - 1
    t = np.zeros(n)
    alive = np.ones(n, bool)          # waiting in the queue
    filled = np.zeros(n, bool)
    tf = np.full(n, np.nan)
    qb, qa = same.astype(int).copy(), opp.astype(int).copy()
    mid = np.zeros(n)
    marking = np.zeros(n, bool)       # after a fill, following the mid
    active = alive.copy()
    regen_cdf = np.cumsum(model.regen)
    while active.any():
        idx = np.flatnonzero(active)
        lb, cb, mb = model.rates(qb[idx])
        la, ca, ma = model.rates(qa[idx])
        tot = lb + cb + mb + la + ca + ma
        dt = rng.exponential(1.0 / tot)
        t[idx] += dt
        u = rng.random(len(idx)) * tot
        ev = np.select([u < lb, u < lb + cb, u < lb + cb + mb, u < lb + cb + mb + la, u < tot - ma], [0, 1, 2, 3, 4], 5)
        w = alive[idx]
        # time limits
        late_wait = w & (t[idx] > tmax)
        late_mark = marking[idx] & (t[idx] > tf[idx] + H)
        ok = ~(late_wait | late_mark)
        i = idx[ok]
        e = ev[ok]
        wi = alive[i]
        # bid side events
        add_b = e == 0
        qb[i[add_b]] += 1
        behind[i[add_b & wi]] += 1
        can = (e == 1) & (qb[i] > 0)
        ci = i[can]
        others = np.maximum(qb[ci] - alive[ci].astype(int), 1)
        pick_ahead = alive[ci] & (rng.random(len(ci)) * others < ahead[ci])
        ahead[ci[pick_ahead]] -= 1
        behind[ci[alive[ci] & ~pick_ahead]] = np.maximum(behind[ci[alive[ci] & ~pick_ahead]] - 1, 0)
        qb[ci] -= 1
        mkt = (e == 2) & (qb[i] > 0)
        mi = i[mkt]
        hit_us = alive[mi] & (ahead[mi] == 0)
        ahead[mi[alive[mi] & ~hit_us]] -= 1
        qb[mi] -= 1
        f = mi[hit_us]
        alive[f], filled[f], marking[f], tf[f] = False, True, True, t[f]
        # ask side events
        qa[i[e == 3]] += 1
        rm = i[(e >= 4) & (qa[i] > 0)]
        qa[rm] -= 1
        # empty queues: the price moves one tick
        up = i[qa[i] == 0]
        gone = up[alive[up]]
        alive[gone] = False                                  # the price moved away before a fill
        mv = up[marking[up]]
        mid[mv] += 1.0
        dn = i[(qb[i] == 0) & marking[i]]
        mid[dn] -= 1.0
        for arr in (up, dn):
            if len(arr):
                qa[arr] = np.searchsorted(regen_cdf, rng.random(len(arr)))
                qb[arr] = np.searchsorted(regen_cdf, rng.random(len(arr)))
        qa[i] = np.maximum(qa[i], 1)
        qb[i] = np.maximum(qb[i], np.where(alive[i], ahead[i] + 1 + behind[i], 1))
        alive[idx[late_wait]] = False
        marking[idx[late_mark]] = False
        active = alive | marking
    pnl = np.where(filled, 0.5 + mid, 0.0)
    fill = filled.reshape(-1, paths).mean(axis=1).reshape(shape)
    value = pnl.reshape(-1, paths).mean(axis=1).reshape(shape)
    with np.errstate(invalid="ignore"):
        adv = np.where(filled, -mid, np.nan).reshape(-1, paths)
        adverse = np.nanmean(adv, axis=1).reshape(shape) if filled.any() else np.full(shape, np.nan)
    return {"fill": fill, "value": value, "adverse": adverse}


def value_table(model: QRModel, qs, H: float = 10.0, tmax: float = 60.0, paths: int = 2000, seed: int = 1) -> dict:
    qs = np.asarray(qs, int)
    same, opp = np.meshgrid(qs, qs, indexing="ij")
    back = order_value(model, same - 1, same, opp, H, tmax, paths, seed)
    front = order_value(model, np.zeros_like(same), same, opp, H, tmax, paths, seed + 1)
    return {"same": same, "opp": opp, "back": back, "front": front}
