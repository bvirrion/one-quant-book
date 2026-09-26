"""firm.latrace -- latency races, sniping and the venue designs that change them (One Quant Book 11, chapter 9).

A race starts when public information makes a resting quote stale: the price has jumped by J ticks, more than the
quote's half-spread h, so hitting the quote earns J - h per share. The liquidity provider sends a cancel; snipers send
orders to take it. Each message reaches the matching engine after a latency drawn per message (lognormal around a
median, in microseconds). The venue decides who wins:

    'continuous'   price-time: the quote is sniped if the first taker arrives before the cancel;
    'symmetric'    every inbound message delayed by d: the same race, shifted;
    'asymmetric'   takers delayed by d, cancels and new quotes not: sniped only if the first taker's latency plus d
                   beats the cancel;
    'batch'        a frequent batch auction with interval tau: messages are processed at the end of the batch they
                   arrive in, cancels first; the quote is sniped only if a taker arrives in an earlier batch than the
                   cancel (the event falls at a uniform point of its batch).

race(...) returns the probability that the provider is sniped, the latency-arbitrage tax per race (expected loss per
share) and, for continuous races, the gap between the winner and the first loser.

The second half is a quoter for firm.mmharness that defends itself with a lead signal: LeadGuard withdraws the side of
a one-lot quote that the leader's move says is stale, for `hold` seconds, reading the leader with its own delay.

API (stable):
    race(design, n, lp_median, sniper_median, snipers, jitter, d, tau, jump, half, seed)
                                                 {'p_sniped', 'tax', 'gap_median'} (microseconds for times, ticks
                                                 per share for the tax)
    LeadGuard(leader_t, leader_mid, lead_delay, move, window, hold, size, limit)
"""
from __future__ import annotations

import numpy as np


def _lat(rng, median: float, jitter: float, size) -> np.ndarray:
    return median * np.exp(jitter * rng.standard_normal(size))


def race(design: str = "continuous", n: int = 100_000, lp_median: float = 50.0, sniper_median: float = 40.0,
         snipers: int = 3, jitter: float = 0.3, d: float = 0.0, tau: float = 1000.0, jump: float = 1.0,
         half: float = 0.5, seed: int = 1) -> dict:
    rng = np.random.default_rng(seed)
    c = _lat(rng, lp_median, jitter, n)
    s = _lat(rng, sniper_median, jitter, (n, snipers))
    first = s.min(axis=1)
    second = np.sort(s, axis=1)[:, 1] if snipers > 1 else np.full(n, np.inf)
    if design in ("continuous", "symmetric"):
        sniped = first < c                             # a symmetric delay shifts both by d
    elif design == "asymmetric":
        sniped = first + d < c
    elif design == "batch":
        u = rng.uniform(0.0, tau, n)
        sniped = np.floor((u + first) / tau) < np.floor((u + c) / tau)
    else:
        raise ValueError(design)
    arrivals = np.column_stack([c, s])
    ordered = np.sort(arrivals, axis=1)
    return {"p_sniped": float(sniped.mean()), "tax": float(sniped.mean() * max(jump - half, 0.0)),
            "gap_median": float(np.median(ordered[:, 1] - ordered[:, 0])),
            "first_loser_gap": float(np.median(second - first))}


class LeadGuard:
    """One lot per side at the others' best prices (at most `limit` shares either way); when the leader's mid, read
    `lead_delay` seconds late, has moved by at least `move` ticks over `window` seconds more than this instrument's,
    withdraw the side that the move makes stale (the ask after an up-move) for `hold` seconds."""

    def __init__(self, leader_t, leader_mid, lead_delay: float = 0.001, move: float = 1.0, window: float = 1.0,
                 hold: float = 1.0, size: int = 100, limit: int = 500, guard: bool = True):
        self.lt, self.lm = np.asarray(leader_t, float), np.asarray(leader_mid, float)
        self.delay, self.move, self.window, self.hold = lead_delay, move, window, hold
        self.size, self.limit, self.guard = size, limit, guard
        self.until = {1: -1.0, -1: -1.0}
        self.own: list = []

    def _lead_mid(self, t: float) -> float:
        i = int(np.searchsorted(self.lt, t - self.delay, side="right")) - 1
        return float(self.lm[max(i, 0)])

    def on_start(self, ctx):
        pass

    def on_market(self, ctx, t, top):
        x = ctx.external(top)
        mid = 0.5 * (x["bid"] + x["ask"])
        self.own.append((t, mid))
        while len(self.own) > 1 and self.own[1][0] <= t - self.window:
            self.own.pop(0)
        if self.guard:
            gap = (self._lead_mid(t) - self._lead_mid(t - self.window)) - (mid - self.own[0][1])
            if gap >= self.move:
                self.until[-1] = t + self.hold
            elif gap <= -self.move:
                self.until[1] = t + self.hold
        bq = self.size if ctx.position + self.size <= self.limit and t >= self.until[1] else 0
        aq = self.size if ctx.position - self.size >= -self.limit and t >= self.until[-1] else 0
        ctx.quote(int(x["bid"]), bq, int(x["ask"]), aq)

    def on_fill(self, ctx, fill):
        pass
