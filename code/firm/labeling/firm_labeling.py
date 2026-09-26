"""firm.labeling -- labels, overlap and sample weights (build of One Quant Book 12, chapter 2).

A label is a statement about the future made at an event time t0 and settled at a later time t1. This module builds
labels from a price path (fixed-horizon and triple-barrier labels, meta-labels), measures how much they overlap
(concurrency and average uniqueness, after Lopez de Prado), and turns the overlap into sample weights and into the
sequential bootstrap. Bars are integer indices 0..n-1 of a series of log returns r; a label starting at bar t0 uses the
returns of bars t0 + 1 .. t1 (the close of bar t0 is the decision time).

API (stable):
    fixed_horizon(r, t0, h)                   -> dict(t1, ret, label)        label = sign of the h-bar return
    triple_barrier(r, t0, up, down, h, side)  -> dict(t1, ret, label, hit)   first touch of +up / -down (log-return
                                                 widths per label) or the vertical barrier t0 + h; label = sign of the
                                                 return at t1 (times side if given); hit in {'up', 'down', 'time'}
    vol_widths(sigma, t0, h, k)               k * sigma[t0] * sqrt(h): widths scaled by the volatility known at t0
    meta_labels(side, ret)                    1 where side * ret > 0 (the primary model's call made money), else 0
    concurrency(t0, t1, n)                    (n,) number of labels whose span (t0, t1] contains each bar
    average_uniqueness(t0, t1, n)             (m,) mean over each label's bars of 1 / concurrency
    attribution_weights(t0, t1, r, n)         (m,) |sum over the label's bars of r / concurrency|, normalised to mean 1
    time_decay(u, last)                       (m,) weights decaying linearly in cumulative uniqueness, oldest = last
    sequential_bootstrap(t0, t1, n, size, rng) indices drawn with probability proportional to their average uniqueness
                                                 given the labels already drawn
"""
from __future__ import annotations

import numpy as np


def fixed_horizon(r, t0, h: int) -> dict:
    r = np.asarray(r, float)
    t0 = np.asarray(t0, int)
    c = np.concatenate([[0.0], np.cumsum(r)])
    t1 = np.minimum(t0 + h, len(r) - 1)
    ret = c[t1 + 1] - c[t0 + 1]
    return {"t1": t1, "ret": ret, "label": np.sign(ret).astype(int)}


def vol_widths(sigma, t0, h: int, k: float = 1.0):
    return k * np.asarray(sigma, float)[np.asarray(t0, int)] * np.sqrt(h)


def triple_barrier(r, t0, up, down, h: int, side=None) -> dict:
    """up, down: positive log-return widths (scalars or per label; np.inf disables a barrier). With a side (+1 long,
    -1 short) the barriers are profit-taking and stop-loss for that position: up is the profit width."""
    r = np.asarray(r, float)
    t0 = np.asarray(t0, int)
    m = len(t0)
    up = np.broadcast_to(np.asarray(up, float), (m,))
    down = np.broadcast_to(np.asarray(down, float), (m,))
    sd = np.ones(m) if side is None else np.asarray(side, float)
    c = np.concatenate([[0.0], np.cumsum(r)])
    t1 = np.empty(m, int)
    ret = np.empty(m)
    hit = np.empty(m, dtype="<U4")
    n = len(r)
    for i in range(m):
        a, b = t0[i], min(t0[i] + h, n - 1)
        path = sd[i] * (c[a + 2:b + 2] - c[a + 1])                     # position return after bars a+1 .. b
        iu = np.flatnonzero(path >= up[i])
        idn = np.flatnonzero(path <= -down[i])
        ju = iu[0] if len(iu) else np.inf
        jd = idn[0] if len(idn) else np.inf
        if ju == jd == np.inf:
            t1[i], hit[i] = b, "time"
        elif ju <= jd:
            t1[i], hit[i] = a + 1 + int(ju), "up"
        else:
            t1[i], hit[i] = a + 1 + int(jd), "down"
        ret[i] = c[t1[i] + 1] - c[a + 1]
    label = np.sign(sd * ret).astype(int)
    return {"t1": t1, "ret": ret, "label": label, "hit": hit}


def meta_labels(side, ret):
    return (np.asarray(side) * np.asarray(ret) > 0).astype(int)


def concurrency(t0, t1, n: int):
    d = np.zeros(n + 1)
    np.add.at(d, np.asarray(t0, int) + 1, 1.0)
    np.add.at(d, np.asarray(t1, int) + 1, -1.0)
    return np.cumsum(d)[:n]


def _span_mean(vals, t0, t1):
    c = np.concatenate([[0.0], np.cumsum(vals)])
    t0, t1 = np.asarray(t0, int), np.asarray(t1, int)
    return (c[t1 + 1] - c[t0 + 1]) / np.maximum(t1 - t0, 1)


def average_uniqueness(t0, t1, n: int):
    cc = concurrency(t0, t1, n)
    return _span_mean(1.0 / np.maximum(cc, 1.0), t0, t1)


def attribution_weights(t0, t1, r, n: int):
    cc = np.maximum(concurrency(t0, t1, n), 1.0)
    c = np.concatenate([[0.0], np.cumsum(np.asarray(r, float)[:n] / cc)])
    t0, t1 = np.asarray(t0, int), np.asarray(t1, int)
    w = np.abs(c[t1 + 1] - c[t0 + 1])
    return w * len(w) / w.sum()


def time_decay(u, last: float = 0.5):
    """Weights linear in cumulative uniqueness: the newest label weighs 1, the oldest `last` (0 < last <= 1)."""
    cu = np.cumsum(np.asarray(u, float))
    x = cu / cu[-1]
    return last + (1 - last) * x


def sequential_bootstrap(t0, t1, n: int, size: int, rng):
    """Draw `size` labels one at a time; each candidate's probability is proportional to its average uniqueness if it
    were added to the labels already drawn (duplicates allowed, as in a bootstrap)."""
    t0, t1 = np.asarray(t0, int), np.asarray(t1, int)
    cc = np.zeros(n)
    out = np.empty(size, int)
    for k in range(size):
        inv = 1.0 / (cc + 1.0)
        u = _span_mean(inv, t0, t1)
        p = u / u.sum()
        i = int(rng.choice(len(p), p=p))
        out[k] = i
        cc[t0[i] + 1:t1[i] + 1] += 1.0
    return out
