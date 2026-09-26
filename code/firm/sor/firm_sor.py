"""firm.sor -- a smart order router: venue model, aggressive sweeps with arrival-time alignment, passive allocation
by Cont and Kukanov's programme, dark-first and anti-gaming rules (build of One Quant Book 10, chapter 18).

Prices in currency, fees in currency per share (positive: the member pays), times in nanoseconds.

API (stable):
    Venue(name, entry_ns, take, make, dark=False)        the router's model of a venue: one-way latency, fees
    send_delays(venues, sync, margin_ns=0)               {venue: delay before sending}: 0 for a spray; for a
                                                         synchronised sweep, max latency - latency (+ margin)
    sweep(quotes, qty, fees=None)                        legs (venue, price, qty) of a buy taking displayed asks
                                                         [(venue, price, qty)], best price first, then lowest fee
                                                         (fees = {venue: take}); None fees: in the quotes' order
    VenueStats()                                         per-venue shares sent and filled; .fill_ratio(v, prior)
                                                         (Beta prior), .rank(venues, fees, tick, prior): venues by
                                                         expected fee-adjusted cost of a share sent there, an
                                                         unfilled share costing a tick more later
    Router(legs, venues, t0_ns, sync, cleanup_tick, ...)  a firm.exchsim Agent: sends the legs as immediate-or-cancel
                                                         buys timed by send_delays, then sends the unfilled rest
                                                         one tick higher to every venue in a second synchronised
                                                         sweep (clean-up); .filled_by_venue, .first_sweep
    Fader(price, qty, venues, name)                      a fast liquidity provider: rests qty at price on every
                                                         venue and cancels everywhere else when one of its orders
                                                         fills
    ck_allocate(X, queues, xi, h, take, rebates, lam_u, lam_o, improve=None, start=None) -> (M, L)
                                                         Cont and Kukanov's order placement: a market order M and
                                                         limit orders L_k behind queues Q_k, minimising the sample
                                                         average of the cost over outflow scenarios xi (samples x
                                                         venues) by a derivative-free search
    ck_cost(M, L, X, queues, xi, h, take, rebates, lam_u, lam_o, improve=None) -> (cost per sample, filled)
    child_sizes(qty, n, rng, spread)                     anti-gaming: n child sizes in round lots, randomised
    dark_first(qty, dark, min_qty)                       the dark legs first, each with a minimum fill quantity
"""
from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "exchsim"))
from firm_exchsim import Agent, Order  # noqa: E402

TICK = 100                                       # 0.01 in the simulator's 1/10,000 units


@dataclass(frozen=True)
class Venue:
    name: str
    entry_ns: int
    take: float = 0.0030
    make: float = -0.0020
    dark: bool = False


def send_delays(venues, sync: bool, margin_ns: int = 0) -> dict:
    far = max(v.entry_ns for v in venues)
    return {v.name: (far - v.entry_ns + margin_ns if sync else 0) for v in venues}


def sweep(quotes, qty: int, fees=None) -> list:
    order = sorted(quotes, key=lambda q: (q[1], fees[q[0]])) if fees is not None else list(quotes)
    out, left = [], qty
    for venue, price, avail in order:
        q = min(avail, left)
        if q > 0:
            out.append((venue, price, q))
            left -= q
    return out


class VenueStats:
    def __init__(self):
        self.sent: dict[str, float] = {}
        self.filled: dict[str, float] = {}

    def add(self, venue: str, sent: float, filled: float) -> None:
        self.sent[venue] = self.sent.get(venue, 0.0) + sent
        self.filled[venue] = self.filled.get(venue, 0.0) + filled

    def fill_ratio(self, venue: str, prior=(1.0, 1.0)) -> float:
        a, b = prior
        return (self.filled.get(venue, 0.0) + a) / (self.sent.get(venue, 0.0) + a + b)

    def rank(self, venues, fees: dict, tick: float = 0.01, prior=(1.0, 1.0)) -> list:
        """(venue, expected cost above the quote per share sent): the take fee when it fills, a tick otherwise."""
        cost = {v: self.fill_ratio(v, prior) * fees[v] + (1 - self.fill_ratio(v, prior)) * tick for v in venues}
        return sorted(cost.items(), key=lambda x: x[1])


class Router(Agent):
    """Sends `legs` (venue, price in simulator units, qty) as immediate-or-cancel buys at t0_ns, timed so that they
    arrive together (sync) or sent at once (spray); when every leg has reported, sends what is left one tick higher
    to every venue in `cleanup` (a synchronised sweep of their second level: {venue: qty})."""

    name = "router"

    def __init__(self, legs, venues, t0_ns: int, sync: bool, cleanup=None, margin_ns: int = 0):
        self.legs, self.venues, self.t0, self.sync = legs, {v.name: v for v in venues}, t0_ns, sync
        self.cleanup, self.margin = cleanup or {}, margin_ns
        self.pending: set[int] = set()
        self.first_sweep = True
        self.filled_by_venue: dict[str, int] = {}
        self.first_filled = 0
        self.cl_venue: dict[int, str] = {}
        self.next_cl = 0

    def on_start(self, ctx):
        self.names = {s.venue: s.name.split("@")[-1] for s in ctx.sessions}
        d = send_delays([self.venues[v] for v, _, _ in self.legs], self.sync, self.margin)
        for i, (v, _, _) in enumerate(self.legs):
            ctx.set_timer(self.t0 + d[v] - ctx.now_ns, ("leg", i))

    def on_timer(self, ctx, tag):
        v, px, q = self.legs[tag[1]] if tag[0] == "leg" else tag[1:]
        self.next_cl += 1                  # ids are per session: unique across venues
        cl = ctx.send(Order(side="B", qty=int(q), price=int(px), tif="I", venue=v,
                            cl_ord_id=self.next_cl))
        self.cl_venue[cl] = v
        if tag[0] == "leg":
            self.pending.add(cl)

    def on_report(self, ctx, rep):
        k = type(rep).__name__
        cl = getattr(rep, "cl_ord_id", None)
        if k == "Out_E":
            v = self.cl_venue.get(cl, "?")
            self.filled_by_venue[v] = self.filled_by_venue.get(v, 0) + rep.qty
            if self.first_sweep:
                self.first_filled += rep.qty
        done = (k == "Out_E" and rep.leaves == 0) or k in ("Out_C", "Out_J")
        if done and cl in self.pending:
            self.pending.discard(cl)
            if not self.pending and self.first_sweep:
                self.first_sweep = False
                self._clean_up(ctx)

    def _clean_up(self, ctx):
        left = sum(q for _, _, q in self.legs) - self.first_filled
        if left <= 0 or not self.cleanup:
            return
        px = max(p for _, p, _ in self.legs) + TICK
        legs = sweep([(v, px, q) for v, q in self.cleanup.items()], left)
        d = send_delays([self.venues[v] for v, _, _ in legs], True)
        for v, p, q in legs:
            ctx.set_timer(d[v], ("clean", v, p, q))


class Fader(Agent):
    """Rests `qty` at `price` (an ask) on every venue in `venues` from start_ns (client id i + 1 on the i-th venue);
    when one of its orders fills, it cancels its orders on all the other venues."""

    def __init__(self, price: int, qty: int, venues, start_ns: int, name: str = "fader"):
        self.price, self.qty, self.venues, self.start, self.name = price, qty, venues, start_ns, name
        self.faded = False

    def on_start(self, ctx):
        ctx.set_timer(self.start - ctx.now_ns, "post")

    def on_timer(self, ctx, tag):
        for i, v in enumerate(self.venues):
            ctx.send(Order(side="S", qty=self.qty, price=self.price, venue=v, cl_ord_id=i + 1))

    def on_report(self, ctx, rep):
        if type(rep).__name__ != "Out_E" or self.faded:
            return
        self.faded = True
        for o in ctx.working():
            if o["cl"] != rep.cl_ord_id:
                ctx.cancel(o["cl"], venue=o["venue"])


# -- passive allocation ------------------------------------------------------------------------------------------
def ck_cost(m, limits, x_total, queues, xi, h, take, rebates, lam_u, lam_o, improve=None):
    """Per-sample cost (currency) of a market order m and limit orders `limits` behind `queues`, against the mid:
    (h + take) m minus (h + rebate_k + improve_k) per share filled at venue k, plus lam_u per share short of X and
    lam_o per share beyond it. A limit order behind Q_k fills min(L_k, (xi_k - Q_k)^+)."""
    xi = np.atleast_2d(np.asarray(xi, float))
    q, lim = np.asarray(queues, float), np.asarray(limits, float)
    r = np.asarray(rebates, float)
    g = np.zeros_like(r) if improve is None else np.asarray(improve, float)
    fill = np.minimum(lim, np.maximum(xi - q, 0.0))
    got = m + fill.sum(axis=1)
    cost = ((h + take) * m - fill @ (h + r + g) + lam_u * np.maximum(x_total - got, 0)
            + lam_o * np.maximum(got - x_total, 0))
    return cost, got


def ck_allocate(x_total, queues, xi, h, take, rebates, lam_u, lam_o, improve=None, start=None):
    """Minimise the sample average of ck_cost over (M, L_1..L_K) in [0, X]^(K+1), the fills being what the scenarios
    give (min(L_k, (xi_k - Q_k)^+)). The objective is piecewise linear and, when the penalties exceed the spread and
    fees (Cont and Kukanov's condition), convex; Powell's derivative-free search from `start` (default: X spread in
    proportion to the expected room ahead of each queue) finds its minimum."""
    from scipy.optimize import minimize

    xi = np.atleast_2d(np.asarray(xi, float))
    k = xi.shape[1]
    if start is None:
        room = np.maximum(xi - np.asarray(queues, float), 0.0).mean(axis=0)
        start = np.r_[0.0, x_total * room / room.sum()]

    def f(z):
        return float(ck_cost(z[0], z[1:], x_total, queues, xi, h, take, rebates, lam_u, lam_o, improve)[0].mean())
    res = minimize(f, np.asarray(start, float), method="Powell", bounds=[(0, x_total)] * (k + 1),
                   options={"xtol": 1e-3, "ftol": 1e-10, "maxfev": 20_000})
    return float(res.x[0]), res.x[1:].copy()


# -- anti-gaming -------------------------------------------------------------------------------------------------
def child_sizes(qty: int, n: int, rng, spread: float = 0.5, lot: int = 100) -> list:
    """n child sizes summing to qty, each a round lot, drawn around qty / n (uniform +- spread of the mean)."""
    w = rng.uniform(1 - spread, 1 + spread, n)
    raw = qty * w / w.sum()
    sizes = np.maximum(lot, np.round(raw / lot) * lot).astype(int)
    sizes[-1] += qty - sizes.sum()
    return [int(x) for x in sizes if x > 0]


def dark_first(qty: int, dark, min_qty: int) -> list:
    """Legs (venue, qty, min_qty) resting the whole quantity in each dark venue first, with a minimum fill quantity
    that stops small pinging orders from discovering it."""
    return [(v, qty, min_qty) for v in dark]
