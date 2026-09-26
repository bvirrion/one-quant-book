"""firm.execalgo -- a complete implementation-shortfall execution algorithm on the exchange simulator (build of One
Quant Book 10, chapter 28): chapter 14's schedule, chapter 17's placement, chapter 18's sweep, chapter 25's halts and
chapter 19's measurement, run as one state machine with pre-trade controls and an audit log.

Prices in the engine's units (1/10,000 of a currency unit, tick 100); quantities in shares; times in seconds from the
parent order's start unless stated.

API (stable):
    Params(side, qty, start_s, horizon_s, urgency, limit, i_would, band, look_s, tol_s, check_s, passive, finish,
           extend_on_pause, max_child, collar_ticks)
        urgency       kappa T of chapter 14's Almgren-Chriss trajectory (0: a straight line, TWAP)
        limit         the worst price the algorithm may pay (buy) or accept (sell); None for none
        i_would       a price at or better than which it trades up to the band's upper edge at once; None for none
        band          (lowest, highest) participation, as a share of the market's volume since the start
        look_s        the passive order rests for the schedule this many seconds ahead
        tol_s         it crosses the spread for what it is behind by more than this many seconds of schedule
        passive       False: market-order children only (the TWAP baseline, with urgency 0 and band (0, 1))
        finish        at the deadline, cross what is left (within the limit) instead of leaving it
        max_child, collar_ticks   pre-trade controls: largest child, farthest child price from the mid
    ISAlgo(params, name="algo", venues=None)   a firm.exchsim Agent. States new -> working <-> paused -> done |
        expired | killed; .log (audit: t_s, state, event, detail), .fills (t_s, price, qty), .arrival (mid at the
        start, engine units), .state, .filled; .kill(t_ns) (use with Simulator.schedule_call). venues: several
        venue names to sweep across with firm.sor.sweep when crossing (one venue by default)
    shortfall_bp(side, fills, arrival, qty, last_mid)   implementation shortfall against the arrival mid, basis
        points of the order's arrival value, the unfilled rest valued at the last mid (opportunity cost)
"""
from __future__ import annotations

import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

for c in ("exchsim", "acexec", "sor"):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / c))
from firm_acexec import ACScheduler  # noqa: E402
from firm_exchsim import SEC, Agent, Order  # noqa: E402
from firm_sor import sweep  # noqa: E402

TICK = 100
T0 = 34_200 * SEC


@dataclass(frozen=True)
class Params:
    side: str = "B"
    qty: int = 10_000
    start_s: float = 60.0
    horizon_s: float = 600.0
    urgency: float = 1.0
    limit: int | None = None
    i_would: int | None = None
    band: tuple = (0.0, 0.3)
    look_s: float = 20.0
    tol_s: float = 20.0
    check_s: float = 1.0
    passive: bool = True
    finish: bool = True
    extend_on_pause: bool = True
    max_child: int = 5_000
    collar_ticks: int = 25


class ISAlgo(Agent):
    def __init__(self, params: Params, name: str = "algo", venues=None):
        self.p, self.name, self.venues = params, name, list(venues or [""])
        self.sched = ACScheduler(params.qty, params.horizon_s, params.urgency / params.horizon_s)
        self.sign = 1 if params.side == "B" else -1
        self.state, self.log, self.fills = "new", [], []
        self.filled, self.mkt_vol, self.paused_s, self.pause_t = 0, 0, 0.0, None
        self.arrival, self.passive_cl, self.ctx, self.wanting = None, None, None, False
        self.cancelled: set = set()
        self.limited = False

    # -- plumbing ---------------------------------------------------------------------------------------------------
    def _t(self, ctx) -> float:
        return (ctx.now_ns - T0) / SEC - self.p.start_s

    def _note(self, ctx, event, detail=""):
        self.log.append((round(self._t(ctx), 3), self.state, event, detail))

    def _touch(self, ctx):
        """The best bid and ask across the venues (the consolidated touch)."""
        tops = [ctx.top(1, v) for v in self.venues]
        bids, asks = [t[0] for t in tops if t[0] is not None], [t[2] for t in tops if t[2] is not None]
        return (max(bids) if bids else None), (min(asks) if asks else None)

    def _mid(self, ctx):
        b, a = self._touch(ctx)
        return None if b is None or a is None else (b + a) / 2

    def _send(self, ctx, qty: int, price: int, tif: str, venue: str = "") -> int | None:
        """Pre-trade controls (child size, price collar around the mid, never more than the order), then send."""
        mid = self._mid(ctx)
        working = sum(o["leaves"] for o in ctx.working() if o["cl"] not in self.cancelled)
        why = None
        if qty > self.p.max_child:
            why = f"child {qty} > {self.p.max_child}"
        elif mid is not None and abs(price - mid) > self.p.collar_ticks * TICK:
            why = f"price {price} outside the collar"
        elif self.filled + working + qty > self.p.qty:
            why = "would exceed the order"
        if why:
            self._note(ctx, "reject", why)
            return None
        return ctx.send(Order(side=self.p.side, qty=qty, price=int(price), tif=tif, venue=venue))

    def _cancel(self, ctx, cl):
        if cl not in self.cancelled:
            ctx.cancel(cl)
            self.cancelled.add(cl)

    def _cancel_all(self, ctx):
        for o in ctx.working():
            self._cancel(ctx, o["cl"])
        self.passive_cl = None

    # -- events -----------------------------------------------------------------------------------------------------
    def on_start(self, ctx):
        self.ctx = ctx
        ctx.set_timer(T0 + int(self.p.start_s * SEC) - ctx.now_ns, "check")

    def on_feed(self, ctx, m):
        kind = type(m).__name__
        if kind in ("Feed_E", "Feed_C") and self.state != "new":
            self.mkt_vol += m.shares
        elif kind == "Feed_H" and self.state in ("working", "paused"):
            if m.state != "T" and self.state == "working":
                self._cancel_all(ctx)
                self.state, self.pause_t = "paused", self._t(ctx)
                self._note(ctx, "pause", f"trading state {m.state}")
            elif m.state == "T" and self.state == "paused":
                if self.p.extend_on_pause:
                    self.paused_s += self._t(ctx) - self.pause_t
                self.state = "working"
                self._note(ctx, "resume", f"schedule shifted by {self.paused_s:.1f} s")

    def on_report(self, ctx, rep):
        if type(rep).__name__ == "Out_E":
            self.filled += rep.qty
            self.fills.append((round(self._t(ctx), 6), rep.price, rep.qty))

    def kill(self, t_ns, *_):
        ctx = self.ctx
        if self.state in ("done", "expired", "killed"):
            return
        self._cancel_all(ctx)
        self.state = "killed"
        self._note(ctx, "kill", f"{self.filled} of {self.p.qty} filled")

    def on_timer(self, ctx, tag):
        if self.state in ("done", "expired", "killed"):
            return
        ctx.set_timer(int(self.p.check_s * SEC), "check")
        if self.state == "new":
            self.arrival = self._mid(ctx)
            self.state = "working"
            self._note(ctx, "start", f"arrival mid {self.arrival}")
        if self.state == "working":
            self.check(ctx)

    # -- the decision -----------------------------------------------------------------------------------------------
    def _band(self, x: float) -> float:
        others = self.mkt_vol - self.filled
        lo, hi = self.p.band
        return float(np.clip(x, lo / (1 - lo) * others, hi / (1 - hi) * others if hi < 1 else math.inf))

    def check(self, ctx):
        p, sgn = self.p, self.sign
        tau = self._t(ctx) - self.paused_s
        left = p.qty - self.filled
        if left <= 0:
            self._cancel_all(ctx)
            self.state = "done"
            self._note(ctx, "done", f"{self.filled} filled")
            return
        b, a = self._touch(ctx)
        if b is None or a is None:
            return
        far, near = (a, b) if sgn > 0 else (b, a)
        if tau >= p.horizon_s:                                      # the deadline
            self._cancel_all(ctx)
            if p.finish and tau < p.horizon_s + p.check_s:
                self._cross(ctx, left, far)
                self._note(ctx, "finish", f"crossing the last {left}")
            else:
                self.state = "expired"
                self._note(ctx, "expire", f"{left} left unfilled")
            return
        now = self._band(p.qty - float(self.sched.targets([tau])[0]))
        if p.i_would is not None and sgn * (p.i_would - far) >= 0:
            now = max(now, min(p.qty, self._band(math.inf)))
            if not self.wanting:
                self._note(ctx, "i-would", f"far touch {far} at or better than {p.i_would}")
            self.wanting = True
        else:
            self.wanting = False
        tol = p.tol_s / p.horizon_s * p.qty if p.passive else 0.0
        behind = int((now - self.filled - tol) // 100) * 100
        if behind >= 100:
            if self.passive_cl is not None:                          # the resting order is re-sized below
                self._cancel(ctx, self.passive_cl)
                self.passive_cl = None
            self._cross(ctx, behind, far)
        if p.passive:
            ahead = self._band(p.qty - float(self.sched.targets([tau + p.look_s])[0]))
            self._rest(ctx, int((min(ahead, p.qty) - self.filled - max(behind, 0)) // 100) * 100, near)

    def _px_ok(self, px: int) -> bool:
        return self.p.limit is None or self.sign * (px - self.p.limit) <= 0

    def _cross(self, ctx, qty: int, far: int):
        """Take qty at the far touch (within the limit): across the venues' displayed quotes, best price first (the
        sweep of chapter 18), any rest on the first venue; children no larger than max_child."""
        if not self._px_ok(far):
            if not self.limited:                                     # log the start of each episode only
                self._note(ctx, "limit", f"far touch {far} beyond the limit {self.p.limit}")
            self.limited = True
            return
        if self.limited:
            self._note(ctx, "limit off", f"far touch {far}")
        self.limited = False
        legs = [(self.venues[0], far, qty)]
        if len(self.venues) > 1:
            quotes = []
            for v in self.venues:
                b, bq, a, aq = ctx.top(1, v)
                px, q = (a, aq) if self.sign > 0 else (b, bq)
                if px is not None and self._px_ok(px):
                    quotes.append((v, self.sign * px, q))
            legs = [(v, self.sign * px, q) for v, px, q in sweep(quotes, qty, {v: 0 for v in self.venues})]
            rest = qty - sum(q for _, _, q in legs)
            if rest > 0:
                legs.append((self.venues[0], far, rest))
        for v, px, q in legs:
            while q > 0:
                c = min(q, self.p.max_child)
                self._send(ctx, c, px, "I", v)
                q -= c

    def _rest(self, ctx, qty: int, near: int):
        """One passive order at the near touch for the schedule ahead (within the limit), replaced when its price
        or size is wrong by a lot or more."""
        px = near if self._px_ok(near) else self.p.limit
        live = {o["cl"]: o for o in ctx.working()}
        cur = live.get(self.passive_cl)
        if cur is not None and cur["price"] == px and abs(cur["leaves"] - qty) < 100:
            return
        if cur is not None:
            self._cancel(ctx, self.passive_cl)
            self.passive_cl = None
        if qty >= 100:
            self.passive_cl = self._send(ctx, min(qty, self.p.max_child), px, "D")


def shortfall_bp(side: str, fills, arrival: float, qty: int, last_mid: float) -> float:
    sgn = 1 if side == "B" else -1
    done = sum(q for _, _, q in fills)
    paid = sum(px * q for _, px, q in fills)
    cost = sgn * (paid - done * arrival) + sgn * (qty - done) * (last_mid - arrival)
    return float(cost / (qty * arrival) * 1e4)
