"""firm.toxicity -- toxicity scores and the market maker's responses (One Quant Book 11, chapter 6).

A toxicity score is the market maker's real-time estimate of the adverse selection of the next fill on one side of
its quotes: here the negative of a linear forecast of the fill's mark-out, from features observable when the quote is
resting. This module holds the pieces that do not depend on a particular market:

* grouped mark-outs with standard errors (by counterparty class, venue, order type, time of day), on firm.markout;
* FlowTracker: streaming features from an order-by-order feed -- signed traded volume against each side over a
  window, the share of each side in the two best queues (others' orders), the time since the mid last changed;
* ToxicityModel: ordinary least squares of mark-outs on features, fitted on one period, a score on the next;
* a Quoter wrapper for firm.mmharness that fades (withdraws) or widens (steps back one tick) the side whose score is
  above a threshold, around any base quoting rule.

API (stable):
    grouped(markouts, qty, groups)                  {group: (mean, standard error)} per horizon, quantity-weighted
    FlowTracker(window)                             .update(t, last_msg, top_ext); .features(side) -> np.ndarray
    FEATURES                                        the names of the feature vector
    ToxicityModel.fit(X, y) -> model; .predict(X); .score(x) = -predicted mark-out (ticks)
    ToxicQuoter(model, mode, threshold, size, limit, record, window, restore)
                                                    mode 'base' (never reacts), 'fade', 'widen'; record=True keeps the
                                                    features at each fill (for fitting); restore: hysteresis, a side
                                                    reacted to stays so until its score falls below restore
"""
from __future__ import annotations

import math
import pathlib
import sys
from collections import deque

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "markout"))
import firm_markout  # noqa: E402

FEATURES = ("flow_against", "queue_against", "log_quiet", "wide")


def grouped(markouts, qty, groups) -> dict:
    return firm_markout.curve(markouts, qty, groups)


class FlowTracker:
    """Streaming features for each side of the quotes. flow_against: aggressive volume (lots) over the last `window`
    seconds that would hit that side (sells for the bid, buys for the ask) minus the opposite; queue_against: the
    other side's share of the two best queues; log_quiet: log(1 + seconds since the mid last changed); wide: 1 if
    the spread exceeds one tick."""

    def __init__(self, window: float = 2.0, lot: int = 100):
        self.window, self.lot = window, lot
        self.trades: deque = deque()
        self.net = 0.0                      # buyer-initiated minus seller-initiated lots in the window
        self.mid = None
        self.t_mid = 0.0
        self.qb = self.qa = 1
        self.spread = 1

    def update(self, t: float, last: dict | None, ext: dict) -> None:
        if last is not None and last["kind"] == b"E":
            v = last["agg"] * last["qty"] / self.lot
            self.trades.append((t, v))
            self.net += v
        while self.trades and self.trades[0][0] < t - self.window:
            self.net -= self.trades.popleft()[1]
        mid = 0.5 * (ext["bid"] + ext["ask"])
        if mid != self.mid:
            self.mid, self.t_mid = mid, t
        self.qb, self.qa = max(int(ext["bid_qty"]), 0), max(int(ext["ask_qty"]), 0)
        self.spread = int(ext["ask"]) - int(ext["bid"])
        self.now = t

    def features(self, side: int) -> np.ndarray:
        tot = self.qb + self.qa
        other = (self.qa if side == 1 else self.qb) / tot if tot else 0.5
        return np.array([-side * self.net, other, math.log1p(self.now - self.t_mid), float(self.spread > 1)])


class ToxicityModel:
    def __init__(self, coef: np.ndarray):
        self.coef = np.asarray(coef, float)

    @classmethod
    def fit(cls, X, y) -> ToxicityModel:
        X = np.column_stack([np.ones(len(X)), np.asarray(X, float)])
        coef, *_ = np.linalg.lstsq(X, np.asarray(y, float), rcond=None)
        return cls(coef)

    def predict(self, X) -> np.ndarray:
        X = np.atleast_2d(np.asarray(X, float))
        return self.coef[0] + X @ self.coef[1:]

    def score(self, x) -> float:
        return float(-self.predict(x)[0])


class ToxicQuoter:
    """Rest `size` shares at the others' best bid and ask (at most `limit` shares either way). mode 'fade' withdraws
    a side whose toxicity score exceeds `threshold`; 'widen' rests it one tick further from the mid instead; 'base'
    ignores the score. With record=True the features of each side are kept at every fill."""

    def __init__(self, model: ToxicityModel | None = None, mode: str = "base", threshold: float = 0.0,
                 size: int = 100, limit: int = 500, record: bool = False, window: float = 2.0,
                 restore: float | None = None):
        self.model, self.mode, self.threshold, self.restore = model, mode, threshold, restore
        self.faded = {1: False, -1: False}
        self.size, self.limit, self.record = size, limit, record
        self.flow = FlowTracker(window, size)
        self.at_fill: list = []
        self.cur = {1: None, -1: None}
        self.scores: list = []

    def on_start(self, ctx):
        pass

    def on_market(self, ctx, t, top):
        x = ctx.external(top)
        self.flow.update(t, ctx.last, x)
        px = {1: int(x["bid"]), -1: int(x["ask"])}
        qty = {1: self.size if ctx.position + self.size <= self.limit else 0,
               -1: self.size if ctx.position - self.size >= -self.limit else 0}
        for s in (1, -1):
            f = self.flow.features(s)
            self.cur[s] = f
            if self.model is not None and self.mode != "base":
                sc = self.model.score(f)
                if self.restore is None:
                    self.faded[s] = sc > self.threshold
                elif sc > self.threshold:
                    self.faded[s] = True
                elif sc < self.restore:
                    self.faded[s] = False
                if self.faded[s]:
                    if self.mode == "fade":
                        qty[s] = 0
                    else:
                        px[s] -= s
        ctx.quote(px[1], qty[1], px[-1], qty[-1])

    def on_fill(self, ctx, fill):
        if self.record and self.cur[fill.side] is not None:
            self.at_fill.append((fill.t, fill.side, *self.cur[fill.side]))
