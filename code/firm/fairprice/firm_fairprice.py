"""firm.fairprice -- streaming fair-price estimators (One Quant Book 11, chapter 2).

A market maker's fair price is its estimate of the efficient price P*_t from everything it sees: the mid and the
queue sizes of each venue, and the prices of related instruments. This module holds the estimators of chapter 2:

* the weighted mid, (ask * bid_qty + bid * ask_qty) / (bid_qty + ask_qty): the side with the larger queue pulls the
  estimate away from itself, towards the price it is less likely to move from;
* a microprice table: the mid plus the average next-horizon mid change by queue-imbalance bucket, fitted on history
  (One Quant Book 7, chapter 8 defines the microprice);
* the fair-price filter: a local-level Kalman filter, P*_t a random walk with variance q per second, observed at
  irregular times by any number of sources (a venue's mid or microprice, a related instrument's price translated into
  this instrument's units), source j with noise variance r_j. Each observation first propagates the variance for the
  elapsed time, then updates:  P += q (t - t_prev);  K = P / (P + r_j);  x += K (y - x);  P = (1 - K) P.
  It is the streaming core: cpp/firm_fairprice.hpp and rust/src/lib.rs implement the same filter, with the same
  operation order, and are checked against data/fixture_*.csv row by row.

Prices are in ticks (floats), times in seconds.

API (stable):
    weighted_mid(bid, bid_qty, ask, ask_qty)       arrays or scalars
    imbalance(bid_qty, ask_qty)                    bid_qty / (bid_qty + ask_qty), in [0, 1]
    fit_micro(imb, spread, dmid, n)                adjustment per imbalance bucket (one-tick spreads only)
    micro(bid, bid_qty, ask, ask_qty, g)           mid + g[bucket]; bucket = min(int(imb * n), n - 1)
    FairFilter(q, r, x0=None, p0=1e6)              r: noise variance per source; update(t, src, y) -> estimate;
                                                   predict(t) -> (estimate, variance); x, p, t
    run_filter(times, srcs, ys, q, r)              the estimate after every observation (numpy array)
    rmse(est, truth)                               root mean squared error
"""
from __future__ import annotations

import math

import numpy as np


def weighted_mid(bid, bid_qty, ask, ask_qty):
    bid, bq, ask, aq = (np.asarray(a, float) for a in (bid, bid_qty, ask, ask_qty))
    return (ask * bq + bid * aq) / (bq + aq)


def imbalance(bid_qty, ask_qty):
    bq, aq = np.asarray(bid_qty, float), np.asarray(ask_qty, float)
    return bq / (bq + aq)


def _bucket(imb, n: int):
    return np.minimum((np.asarray(imb, float) * n).astype(int), n - 1)


def fit_micro(imb, spread, dmid, n: int = 5) -> np.ndarray:
    """Mean mid change over the fitting horizon by imbalance bucket, on one-tick spreads."""
    imb, spread, dmid = (np.asarray(a, float) for a in (imb, spread, dmid))
    sel = (spread == 1) & np.isfinite(dmid)
    b = _bucket(imb[sel], n)
    g = np.zeros(n)
    for k in range(n):
        if (b == k).any():
            g[k] = float(dmid[sel][b == k].mean())
    return g


def micro(bid, bid_qty, ask, ask_qty, g) -> np.ndarray:
    g = np.asarray(g, float)
    mid = 0.5 * (np.asarray(bid, float) + np.asarray(ask, float))
    return mid + g[_bucket(imbalance(bid_qty, ask_qty), len(g))]


class FairFilter:
    """Local-level Kalman filter over irregular observations from several sources."""

    def __init__(self, q: float, r, x0: float | None = None, p0: float = 1e6):
        self.q, self.r = float(q), [float(v) for v in r]
        self.x = math.nan if x0 is None else float(x0)
        self.p, self.t = float(p0), None

    def update(self, t: float, src: int, y: float) -> float:
        if self.t is None:
            self.t = t
            if math.isnan(self.x):
                self.x = y
                self.p = self.r[src]
                return self.x
        self.p += self.q * (t - self.t)
        self.t = t
        k = self.p / (self.p + self.r[src])
        self.x += k * (y - self.x)
        self.p = (1.0 - k) * self.p
        return self.x

    def predict(self, t: float) -> tuple[float, float]:
        return self.x, self.p + self.q * (t - self.t)


def run_filter(times, srcs, ys, q: float, r) -> np.ndarray:
    f = FairFilter(q, r)
    return np.array([f.update(float(t), int(s), float(y)) for t, s, y in zip(times, srcs, ys, strict=True)])


def rmse(est, truth) -> float:
    d = np.asarray(est, float) - np.asarray(truth, float)
    return float(np.sqrt(np.mean(d * d)))
