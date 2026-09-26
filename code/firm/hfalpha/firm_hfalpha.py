"""firm.hfalpha -- short-horizon alpha for a market maker (One Quant Book 11, chapter 7).

A forecast of an instrument's mid over the next seconds, built from its own book and trades and from a related
instrument that moves first, and two ways of using it in quoting: a forecast skew (withdraw the side the forecast says
will be picked off) and a take threshold (cross the spread when the forecast exceeds the cost of crossing).

* Features (streaming, one update per message of the instrument, the leader read as of the same time):
      imbalance  (Q^b - Q^a) / (Q^b + Q^a) at the best prices;
      ofi        order-flow imbalance of Cont, Kukanov and Stoikov over the last `window` seconds (lots);
      flow       buyer- minus seller-initiated volume over the window (lots);
      lead       the leader's mid change over the window (ticks);
      own        the instrument's own mid change over the window (ticks).
  The same FeatureEngine runs offline over a stored message stream (to fit) and online inside a Quoter (to trade).
* Forecast: ridge regression of the mid change over the horizon on the features, fitted on one period.
* Couplings as Quoters for firm.mmharness: AlphaQuoter(model, skew, take, lag) rests one lot per side at the best
  prices, withdraws the side against a forecast beyond `skew` ticks, and takes one lot when the forecast exceeds
  `take` ticks (half the spread plus the taker fee plus a margin); lag = 1 uses the previous message's forecast (the
  forecast one message late).

API (stable):
    FEATURES                                        feature names
    FeatureEngine(window, lot, leader=(t, mid))     .update(t, kind, agg, qty, bid, bid_qty, ask, ask_qty) -> features
    stream(tape, window, leader)                    features after every message of a firm.tape Tape: (times, X, mid)
    target(times, mid, horizon)                     mid change over the next `horizon` seconds (nan at the end)
    Ridge.fit(X, y, lam) -> model; .predict(X); .coef, .intercept, .mean, .scale
    ic(pred, y)                                     Pearson correlation, nan-safe
    AlphaQuoter(model, window, leader, skew, take, lag, size, limit)
"""
from __future__ import annotations

from collections import deque

import numpy as np

FEATURES = ("imbalance", "ofi", "flow", "lead", "own")


class FeatureEngine:
    def __init__(self, window: float = 1.0, lot: int = 100, leader=None):
        self.window, self.lot = window, lot
        self.leader = None if leader is None else (np.asarray(leader[0], float), np.asarray(leader[1], float))
        self.ofi_q: deque = deque()
        self.flow_q: deque = deque()
        self.mid_q: deque = deque()
        self.ofi = self.flow = 0.0
        self.prev = None

    def _lead(self, t: float) -> float:
        if self.leader is None:
            return 0.0
        ts, ms = self.leader
        i = np.searchsorted(ts, [t, t - self.window], side="right") - 1
        i = np.clip(i, 0, len(ms) - 1)
        return float(ms[i[0]] - ms[i[1]])

    def update(self, t, kind, agg, qty, bid, bid_qty, ask, ask_qty) -> np.ndarray:
        bq, aq = bid_qty / self.lot, ask_qty / self.lot
        if self.prev is not None:
            pb, pbq, pa, paq = self.prev
            e = (bq if bid >= pb else 0.0) - (pbq if bid <= pb else 0.0) - (aq if ask <= pa else 0.0) \
                + (paq if ask >= pa else 0.0)
            if e:
                self.ofi_q.append((t, e))
                self.ofi += e
        self.prev = (bid, bq, ask, aq)
        if kind == b"E":
            v = agg * qty / self.lot
            self.flow_q.append((t, v))
            self.flow += v
        for q, name in ((self.ofi_q, "ofi"), (self.flow_q, "flow")):
            while q and q[0][0] < t - self.window:
                setattr(self, name, getattr(self, name) - q.popleft()[1])
        mid = 0.5 * (bid + ask)
        self.mid_q.append((t, mid))
        while len(self.mid_q) > 1 and self.mid_q[1][0] <= t - self.window:
            self.mid_q.popleft()
        own = mid - self.mid_q[0][1]
        imb = (bq - aq) / (bq + aq) if bq + aq else 0.0
        return np.array([imb, self.ofi, self.flow, self._lead(t), own])


def stream(tape, window: float = 1.0, leader=None):
    """Features after every message of a firm.tape Tape (after the opening snapshot)."""
    eng = FeatureEngine(window, tape.cfg.lot, leader)
    m, top = tape.msgs[tape.n_open:], tape.top[tape.n_open:]
    X = np.empty((len(m), len(FEATURES)))
    for i in range(len(m)):
        X[i] = eng.update(float(m["t"][i]), m["kind"][i], int(m["agg"][i]), int(m["qty"][i]), int(top["bid"][i]),
                          int(top["bid_qty"][i]), int(top["ask"][i]), int(top["ask_qty"][i]))
    return m["t"].astype(float), X, 0.5 * (top["bid"] + top["ask"]).astype(float)


def target(times, mid, horizon: float) -> np.ndarray:
    times, mid = np.asarray(times, float), np.asarray(mid, float)
    j = np.searchsorted(times, times + horizon, side="right") - 1
    y = mid[j] - mid
    y[times + horizon > times[-1]] = np.nan
    return y


class Ridge:
    def __init__(self, coef, intercept, mean, scale):
        self.coef, self.intercept, self.mean, self.scale = (np.asarray(coef, float), float(intercept),
                                                             np.asarray(mean, float), np.asarray(scale, float))

    @classmethod
    def fit(cls, X, y, lam: float = 1.0) -> Ridge:
        X, y = np.asarray(X, float), np.asarray(y, float)
        ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
        X, y = X[ok], y[ok]
        mean, scale = X.mean(axis=0), X.std(axis=0)
        scale[scale == 0] = 1.0
        Z = (X - mean) / scale
        b = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))
        return cls(b, y.mean(), mean, scale)

    def predict(self, X) -> np.ndarray:
        Z = (np.atleast_2d(np.asarray(X, float)) - self.mean) / self.scale
        return self.intercept + Z @ self.coef


def ic(pred, y) -> float:
    pred, y = np.asarray(pred, float), np.asarray(y, float)
    ok = np.isfinite(pred) & np.isfinite(y)
    return float(np.corrcoef(pred[ok], y[ok])[0, 1])


class AlphaQuoter:
    """One lot per side at the others' best prices, at most `limit` shares either way. skew: withdraw the ask when the
    forecast exceeds +skew ticks and the bid when it is below -skew. take: buy (sell) one lot at the market when the
    forecast exceeds +take (is below -take) ticks. lag: act on the forecast of `lag` messages earlier."""

    def __init__(self, model: Ridge | None, window: float = 1.0, leader=None, skew: float | None = None,
                 take: float | None = None, lag: int = 0, size: int = 100, limit: int = 500, cooldown: float = 1.0):
        self.model, self.skew, self.take, self.lag = model, skew, take, lag
        self.size, self.limit, self.cooldown = size, limit, cooldown
        self.eng = FeatureEngine(window, size, leader)
        self.hist: deque = deque(maxlen=lag + 1)
        self.last_take = -1e9
        self.takes = 0

    def on_start(self, ctx):
        pass

    def on_market(self, ctx, t, top):
        m, x = ctx.last, ctx.external(top)         # the book without our own orders, as the model was fitted
        f = self.eng.update(t, m["kind"], m["agg"], m["qty"], int(x["bid"]), int(x["bid_qty"]), int(x["ask"]),
                            int(x["ask_qty"]))
        self.hist.append(float(self.model.predict(f)[0]) if self.model is not None else 0.0)
        fc = self.hist[0]
        bq = self.size if ctx.position + self.size <= self.limit else 0
        aq = self.size if ctx.position - self.size >= -self.limit else 0
        if self.skew is not None:
            if fc > self.skew:
                aq = 0
            elif fc < -self.skew:
                bq = 0
        ctx.quote(int(x["bid"]), bq, int(x["ask"]), aq)
        if self.take is not None and t - self.last_take > self.cooldown:
            if fc > self.take and ctx.position + self.size <= self.limit:
                ctx.take(1, self.size)
                self.last_take, self.takes = t, self.takes + 1
            elif fc < -self.take and ctx.position - self.size >= -self.limit:
                ctx.take(-1, self.size)
                self.last_take, self.takes = t, self.takes + 1

    def on_fill(self, ctx, fill):
        pass
