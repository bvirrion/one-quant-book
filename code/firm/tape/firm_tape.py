"""firm.tape -- a synthetic message-level market (build of One Quant Book 7, chapter 2).

The book's standard intraday data: one instrument (or two, the second following the first with a
latency), simulated order by order and written as ITCH-like messages. The mechanism, in ticks:

* an efficient price V jumps by one or two ticks at Poisson times (faster, and by up to three ticks,
  inside a news window); nobody sees it, the informed traders act on it;
* liquidity providers add limit orders at the ten best levels of each side, and inside the spread
  when it is wider than one tick (on the side the efficient price favours); every resting order
  cancels at a constant rate, and faster when the efficient price has moved through its level
  (a stale quote);
* noise traders send market orders at a Hawkes intensity (clustering); most are children of one of
  a few metaorders running at once, of Pareto-distributed length, so order signs have long memory;
* informed traders send market orders at a rate proportional to the distance between V and the mid,
  towards V; they are why a passive fill loses money on average (adverse selection).

Rates are piecewise constant between events except the Hawkes part, simulated exactly by thinning;
every rate (and the efficient price's jump rate) is scaled by an optional U-shaped intraday profile
and by a random activity level, persistent over minutes, so that volume and volatility move together.
Everything is seeded and deterministic.

Messages (numpy structured array `msgs`, one row per message):
    t (float seconds), kind (b'A' add, b'X' cancel, b'E' execution), oid, side (+1 bid, -1 ask:
    the side of the resting order), price (int ticks), qty (shares), agg (+1 buyer-initiated,
    -1 seller-initiated, 0 for A and X), trade (trade id, -1 for A and X)
Also: `trades` (t, price, qty, sign, informed, trade), `top` (t, bid, bid_qty, ask, ask_qty) after
every message, and the efficient-price path `v_t`, `v`. The first `n_open` messages are the opening snapshot.

API (stable):
    TapeConfig(...)                       parameters (defaults: one hour, 100.00, tick 0.01)
    simulate(cfg, v_path=None, agent=None) -> Tape
                                          one instrument; v_path = (times, values[, activity]) imposes V;
                                          agent: a trader inside the market (chapter 19, below)
    activity(cfg, rng)                    the activity multiplier on its grid (mean one)
    simulate_pair(cfg, latency, seed_b)   (Tape A, Tape B): B's efficient price is A's delayed
    Book()                                order book rebuilt from messages: apply(row), best(), depth(side, n)

An agent (Book 7, chapter 19) trades inside the simulated market, the stand-in for live trading: its orders are real
orders in the book, matched in time priority, seen by the other traders (they are never cancelled by the background
flow), and it sees the market and acts with latencies it draws itself. It implements delay_data(), delay_entry(),
on_market(t, top) and on_fill(t, cid, side, price, qty, passive), the last two returning actions:
('limit', cid, side, price, qty), ('cancel', cid), ('market', cid, side, qty). The tape then carries `own` (the
agent's order ids) and `agent_fills` (t, cid, side, price, qty, passive).
"""
from __future__ import annotations

import bisect
import heapq
import itertools
import math
from collections import deque
from dataclasses import dataclass, replace

import numpy as np

MSG = np.dtype([("t", "f8"), ("kind", "S1"), ("oid", "i8"), ("side", "i1"), ("price", "i8"),
                ("qty", "i8"), ("agg", "i1"), ("trade", "i8")])
TRD = np.dtype([("t", "f8"), ("price", "i8"), ("qty", "i8"), ("sign", "i1"), ("informed", "?"), ("trade", "i8")])
TOP = np.dtype([("t", "f8"), ("bid", "i8"), ("bid_qty", "i8"), ("ask", "i8"), ("ask_qty", "i8")])


@dataclass(frozen=True)
class TapeConfig:
    seconds: float = 3600.0
    tick: float = 0.01
    start: int = 10_000                 # opening efficient price, ticks ($100.00)
    lot: int = 100                      # shares per lot
    levels: int = 10
    lo_rate: float = 1.4                # limit orders per second joining the best level, per side
    lo_decay: float = 0.85              # rate at depth k is lo_rate * lo_decay**k
    in_spread: float = 3.0              # per second, when the spread exceeds one tick
    lo_mean_lots: float = 2.0           # mean size of a limit order (geometric)
    cancel: float = 0.04                # per resting order per second
    stale: float = 0.6                  # extra cancel rate per tick the efficient price is through the level
    noise_mu: float = 0.35              # baseline noise market orders per second (both sides)
    hawkes_alpha: float = 0.8           # excitation per noise order
    hawkes_beta: float = 2.0            # decay per second (branching ratio alpha / beta)
    meta_share: float = 0.8             # share of noise orders that are children of a metaorder
    meta_slots: int = 4                 # metaorders running at once
    meta_min: int = 2                   # minimum metaorder length (children)
    meta_tail: float = 1.5              # Pareto tail exponent of metaorder lengths
    mo_mean_lots: float = 1.5
    informed: float = 0.25              # informed orders per second per tick of |V - mid|
    v_rate: float = 0.12                # efficient-price jumps per second
    news_at: float | None = 1800.0      # start of the news window (seconds), or None
    news_len: float = 90.0
    news_mult: float = 8.0
    news_noise: float = 3.0             # noise order rate multiplier inside the news window
    u_shape: float = 0.0                # intraday multiplier 1 + u_shape * (2 t / seconds - 1) ** 2
    act_vol: float = 0.8                # activity a(t) = exp(X), X an Ornstein-Uhlenbeck process of this
    act_half_life: float = 600.0        #   stationary volatility and half-life (seconds), mean one,
    act_step: float = 10.0              #   held constant on steps of act_step seconds
    seed: int = 7


@dataclass
class Tape:
    cfg: TapeConfig
    msgs: np.ndarray
    trades: np.ndarray
    top: np.ndarray
    v_t: np.ndarray
    v: np.ndarray
    n_open: int = 0                               # messages of the opening snapshot (all at t = 0)
    act: np.ndarray | None = None                 # activity multiplier on the act_step grid
    own: np.ndarray | None = None                 # the agent's order ids (chapter 19)
    agent_fills: np.ndarray | None = None         # (t, cid, side, price, qty, passive) of the agent's fills

    def mid(self) -> np.ndarray:
        return 0.5 * (self.top["bid"] + self.top["ask"])


def _geom(rng, mean_lots: float, lot: int) -> int:
    return lot * int(rng.geometric(1.0 / mean_lots))


def _pareto_len(rng, tail: float, lo: int) -> int:
    return int(math.floor(lo * (1.0 - rng.random()) ** (-1.0 / tail)))


def activity(cfg: TapeConfig, rng) -> np.ndarray:
    """Activity multiplier on a grid of act_step seconds: exp(X - var / 2), X a stationary
    Ornstein-Uhlenbeck process sampled exactly, so that E[a] = 1. It scales every rate: busy periods
    have more orders, more trades and a faster efficient price, together (stochastic volatility)."""
    n = int(math.ceil(cfg.seconds / cfg.act_step)) + 1
    if cfg.act_vol <= 0.0:
        return np.ones(n)
    phi = 0.5 ** (cfg.act_step / cfg.act_half_life)
    x = np.empty(n)
    x[0] = rng.normal(0.0, cfg.act_vol)
    eps = rng.normal(0.0, cfg.act_vol * math.sqrt(1.0 - phi * phi), n)
    for k in range(1, n):
        x[k] = phi * x[k - 1] + eps[k]
    return np.exp(x - 0.5 * cfg.act_vol**2)


def efficient_path(cfg: TapeConfig, rng, act=None) -> tuple[np.ndarray, np.ndarray]:
    """Jump times and levels of V (ticks); jumps of 1 or 2 ticks, up to 3 inside the news window. The
    jump rate follows the intraday profile and the activity multiplier."""
    act = activity(cfg, rng) if act is None else act
    t, v, ts, vs = 0.0, float(cfg.start), [0.0], [float(cfg.start)]
    news_edges = [] if cfg.news_at is None else [cfg.news_at, cfg.news_at + cfg.news_len]
    while True:
        news = cfg.news_at is not None and cfg.news_at <= t < cfg.news_at + cfg.news_len
        rate = cfg.v_rate * _mult(cfg, t, act) * (cfg.news_mult if news else 1.0)
        grid = (math.floor(t / cfg.act_step) + 1) * cfg.act_step
        prev, t = t, t + rng.exponential(1.0 / rate)
        crossed = [e for e in news_edges + [grid] if prev < e <= t]
        if crossed:                                  # the rate changes at the edge: restart there
            t = min(crossed)
            continue
        if t >= cfg.seconds:
            break
        size = int(rng.integers(1, 4)) if news else (1 if rng.random() < 0.8 else 2)
        v += size * (1 if rng.random() < 0.5 else -1)
        ts.append(t)
        vs.append(v)
    return np.array(ts), np.array(vs)


def _season(cfg: TapeConfig, t: float) -> float:
    return 1.0 + cfg.u_shape * (2.0 * t / cfg.seconds - 1.0) ** 2


def _mult(cfg: TapeConfig, t: float, act) -> float:
    return _season(cfg, t) * act[min(int(t / cfg.act_step), len(act) - 1)]


AFILL = np.dtype([("t", "f8"), ("cid", "i8"), ("side", "i1"), ("price", "i8"), ("qty", "i8"), ("passive", "?")])


class _Sim:
    def __init__(self, cfg: TapeConfig, v_path, agent=None):
        self.cfg, self.rng = cfg, np.random.default_rng(cfg.seed)
        self.agent, self.aq, self.aseq = agent, [], 0
        self.own: dict[int, int] = {}             # our order id -> client id
        self.cid_oid: dict[int, int] = {}
        self.afills: list = []
        if v_path is None:
            self.act = activity(cfg, self.rng)
            self.v_t, self.v = efficient_path(cfg, self.rng, self.act)
        elif len(v_path) == 3:
            self.v_t, self.v, self.act = v_path
        else:
            self.v_t, self.v = v_path
            self.act = np.ones(int(math.ceil(cfg.seconds / cfg.act_step)) + 1)
        self.vi = 0
        self.book = {1: {}, -1: {}}              # side -> price -> deque[[oid, qty]]
        self.where: dict[int, tuple[int, int]] = {}
        self.pool: list[int] = []                 # every resting order id, for uniform cancellation
        self.pidx: dict[int, int] = {}
        self.oid, self.tid = 0, 0
        self.msgs, self.trades, self.top = [], [], []
        self.h = 0.0                              # Hawkes excitation
        self.meta = [[0, 1] for _ in range(cfg.meta_slots)]    # [children left, sign] per running metaorder
        start = int(round(self.v[0]))
        self.seeding = True
        for k in range(cfg.levels):               # the opening snapshot: a symmetric book, spread one tick
            for side, px in ((1, start - k), (-1, start + 1 + k)):
                for _ in range(3):
                    self._add(0.0, side, px, _geom(self.rng, cfg.lo_mean_lots, cfg.lot))
        self.seeding = False
        self.n_open = len(self.msgs)
        snap = self._top(0.0)
        self.top = [snap] * self.n_open           # snapshot rows carry the top of the complete opening book

    # -- book primitives ----------------------------------------------------------------
    def best(self, side: int) -> int:
        levels = self.book[side]
        return max(levels) if side == 1 else min(levels)

    def _add(self, t, side, px, qty, cid=None):
        self.oid += 1
        self.book[side].setdefault(px, deque()).append([self.oid, qty])
        self.where[self.oid] = (side, px)
        if cid is None:
            self.pidx[self.oid] = len(self.pool)
            self.pool.append(self.oid)
        else:                                      # the agent's order: never in the background cancellation pool
            self.own[self.oid], self.cid_oid[cid] = cid, self.oid
        self._emit(t, b"A", self.oid, side, px, qty, 0, -1)

    def _unpool(self, oid):
        if oid in self.own:
            return
        i, last = self.pidx.pop(oid), self.pool.pop()
        if last != oid:
            self.pool[i], self.pidx[last] = last, i

    def _cancel(self, t, side, px, idx):
        q = self.book[side][px]
        oid, qty = q[idx]
        del q[idx]
        if not q:
            del self.book[side][px]
        del self.where[oid]
        self._unpool(oid)
        self._emit(t, b"X", oid, side, px, qty, 0, -1)

    def _market(self, t, sign, qty, informed):
        side = -sign                               # a buy hits the asks
        self.tid += 1
        while qty > 0 and self.book[side]:
            px = self.best(side)
            q = self.book[side][px]
            oid, rest = q[0]
            fill = min(rest, qty)
            qty -= fill
            if fill == rest:
                q.popleft()
                del self.where[oid]
                self._unpool(oid)
                if not q:
                    del self.book[side][px]
            else:
                q[0][1] -= fill
            self._emit(t, b"E", oid, side, px, fill, sign, self.tid)
            self.trades.append((t, px, fill, sign, informed, self.tid))
            if self.agent is not None:
                if oid in self.own:
                    self._agent_fill(t, self.own[oid], side, px, fill, True)
                if informed is None:                   # the agent's own market order
                    self._agent_fill(t, self._taker, sign, px, fill, False)

    def _emit(self, t, kind, oid, side, px, qty, agg, trade):
        self.msgs.append((t, kind, oid, side, px, qty, agg, trade))
        if not self.seeding:
            self.top.append(self._top(t))
            if self.agent is not None:
                self._apush(t + self.agent.delay_data(), 0, self.top[-1])

    # -- the agent (chapter 19) -----------------------------------------------------------
    def _apush(self, t, kind, payload):
        heapq.heappush(self.aq, (t, kind, self.aseq, payload))
        self.aseq += 1

    def _agent_fill(self, t, cid, side, px, qty, passive):
        self.afills.append((t, cid, side, px, qty, passive))
        self._apush(t + self.agent.delay_data(), 1, (t, cid, side, px, qty, passive))

    def _schedule(self, t, actions):
        for a in actions or ():
            self._apush(t + self.agent.delay_entry(), 2, a)

    def _agent_event(self, t, kind, payload):
        if kind == 0:
            self._schedule(t, self.agent.on_market(t, payload))
        elif kind == 1:
            self._schedule(t, self.agent.on_fill(*payload))
        elif payload[0] == "limit":
            _, cid, side, px, qty = payload
            self._add(t, side, int(px), int(qty), cid)
        elif payload[0] == "cancel":
            oid = self.cid_oid.get(payload[1])
            if oid is not None and oid in self.where:
                side, px = self.where[oid]
                q = self.book[side][px]
                idx = next(i for i, o in enumerate(q) if o[0] == oid)
                if len(q) > 1 or len(self.book[side]) > 1:
                    self._cancel(t, side, px, idx)
        else:
            _, cid, side, qty = payload
            self._taker = cid
            self._market(t, side, int(qty), None)

    def _top(self, t):
        b, a = self.book[1], self.book[-1]
        bb, ba = max(b), min(a)
        return (t, bb, sum(o[1] for o in b[bb]), ba, sum(o[1] for o in a[ba]))

    # -- the event loop -----------------------------------------------------------------
    def run(self):
        cfg, rng = self.cfg, self.rng
        w_lo = [cfg.lo_decay**k for k in range(cfg.levels)]
        cum_lo = list(itertools.accumulate(w_lo))
        lo_total = 2.0 * cfg.lo_rate * cum_lo[-1]
        t = 0.0
        while True:
            while self.vi + 1 < len(self.v_t) and self.v_t[self.vi + 1] <= t:
                self.vi += 1
            V = self.v[self.vi]
            s = _mult(cfg, t, self.act)
            news = cfg.news_at is not None and cfg.news_at <= t < cfg.news_at + cfg.news_len
            bids, asks = self.book[1], self.book[-1]
            bb, ba = max(bids), min(asks)
            gap = V - 0.5 * (bb + ba)
            # piecewise-constant rates by component, then the Hawkes part by thinning
            r_lo = s * lo_total
            r_in = s * cfg.in_spread if ba - bb > 1 else 0.0
            r_cx = cfg.cancel * len(self.pool)
            stale = []                               # levels the efficient price has moved through
            px = bb
            while px > V and px in bids:
                stale.append((1, px, len(bids[px]) * cfg.stale * (px - V)))
                px -= 1
            px = ba
            while px < V and px in asks:
                stale.append((-1, px, len(asks[px]) * cfg.stale * (V - px)))
                px += 1
            r_st = sum(x[2] for x in stale)
            r_inf = s * cfg.informed * abs(gap) if abs(gap) > 0.5 else 0.0
            base = r_lo + r_in + r_cx + r_st + r_inf
            mu = s * cfg.noise_mu * (cfg.news_noise if news else 1.0)
            bound = base + mu + self.h
            dt = rng.exponential(1.0 / bound)
            edge = min(cfg.seconds, (math.floor(t / cfg.act_step) + 1) * cfg.act_step)
            if self.vi + 1 < len(self.v_t):
                edge = min(edge, self.v_t[self.vi + 1])
            if cfg.news_at is not None:
                for e in (cfg.news_at, cfg.news_at + cfg.news_len):
                    if t < e < edge:
                        edge = e
            if self.aq and self.aq[0][0] < min(t + dt, edge):    # the agent acts first: redraw after it
                te, kind, _, payload = heapq.heappop(self.aq)
                te = max(te, t)
                self.h *= math.exp(-cfg.hawkes_beta * (te - t))
                t = te
                self._agent_event(t, kind, payload)
                for sd in (1, -1):
                    while len(self.book[sd]) < 2:
                        far = min(self.book[sd]) - 1 if sd == 1 else max(self.book[sd]) + 1
                        self._add(t, sd, far, _geom(rng, cfg.lo_mean_lots, cfg.lot))
                continue
            if t + dt >= edge:                     # no event before the state changes: move to the edge
                self.h *= math.exp(-cfg.hawkes_beta * (edge - t))
                t = edge
                if t >= cfg.seconds:
                    break
                continue
            t += dt
            self.h *= math.exp(-cfg.hawkes_beta * dt)
            u = rng.random() * bound
            if u >= base + mu + self.h:           # thinning rejection
                continue
            if u >= base:                          # a noise market order
                self.h += cfg.hawkes_alpha
                if rng.random() < cfg.meta_share:
                    slot = self.meta[int(rng.integers(cfg.meta_slots))]
                    if slot[0] == 0:                     # that metaorder is done: a new one starts
                        slot[0] = _pareto_len(rng, cfg.meta_tail, cfg.meta_min)
                        slot[1] = 1 if rng.random() < 0.5 else -1
                    slot[0] -= 1
                    sign = slot[1]
                else:
                    sign = 1 if rng.random() < 0.5 else -1
                self._market(t, sign, _geom(rng, cfg.mo_mean_lots, cfg.lot), False)
            elif u < r_lo:                          # a limit order at depth k of one side
                side = 1 if u < 0.5 * r_lo else -1
                x = (u if side == 1 else u - 0.5 * r_lo) / (s * cfg.lo_rate)
                k = min(bisect.bisect_right(cum_lo, x), cfg.levels - 1)
                self._add(t, side, (bb - k) if side == 1 else (ba + k), _geom(rng, cfg.lo_mean_lots, cfg.lot))
            elif u < r_lo + r_in:                   # inside the spread, on the side the efficient price favours
                if rng.random() < 1.0 / (1.0 + math.exp(-2.0 * gap)):
                    self._add(t, 1, bb + 1, _geom(rng, cfg.lo_mean_lots, cfg.lot))
                else:
                    self._add(t, -1, ba - 1, _geom(rng, cfg.lo_mean_lots, cfg.lot))
            elif u < r_lo + r_in + r_cx:            # a background cancellation of a random resting order
                side, px = self.where[self.pool[int(rng.integers(len(self.pool)))]]
                self._cancel_some(t, side, px, rng)
            elif u < r_lo + r_in + r_cx + r_st:     # a stale quote is pulled
                x = u - (r_lo + r_in + r_cx)
                j = 0
                while j < len(stale) - 1 and x >= stale[j][2]:
                    x -= stale[j][2]
                    j += 1
                self._cancel_some(t, stale[j][0], stale[j][1], rng)
            else:                                   # an informed market order, towards V
                self._market(t, 1 if gap > 0 else -1, _geom(rng, 1.2, cfg.lot), True)
            for sd in (1, -1):                      # keep both sides deep enough to walk
                while len(self.book[sd]) < 2:
                    far = min(self.book[sd]) - 1 if sd == 1 else max(self.book[sd]) + 1
                    self._add(t, sd, far, _geom(rng, cfg.lo_mean_lots, cfg.lot))
        trades = [(a, b, c, d, bool(e), f) for a, b, c, d, e, f in self.trades]
        return Tape(cfg, np.array(self.msgs, dtype=MSG), np.array(trades, dtype=TRD),
                    np.array(self.top, dtype=TOP), np.asarray(self.v_t), np.asarray(self.v), self.n_open,
                    np.asarray(self.act), np.array(sorted(self.own), dtype=np.int64) if self.agent else None,
                    np.array(self.afills, dtype=AFILL) if self.agent else None)

    def _cancel_some(self, t, side, px, rng):
        q = self.book[side][px]
        if len(q) > 1 or len(self.book[side]) > 1:     # never empty a side
            i = int(rng.integers(len(q)))
            if self.agent is not None and q[i][0] in self.own:
                return                                 # the background flow never cancels the agent's orders
            self._cancel(t, side, px, i)


def simulate(cfg: TapeConfig | None = None, v_path=None, agent=None) -> Tape:
    return _Sim(cfg or TapeConfig(), v_path, agent).run()


def simulate_pair(cfg: TapeConfig | None = None, latency: float = 0.05, seed_b: int = 11):
    """Two instruments on one efficient price: B's V is A's delayed by `latency` seconds (an ETF
    that follows its index future). Their liquidity and noise flows are independent."""
    cfg = cfg or TapeConfig()
    rng = np.random.default_rng(cfg.seed + 1000)
    act = activity(cfg, rng)
    vt, v = efficient_path(cfg, rng, act)
    a = simulate(cfg, (vt, v, act))
    shifted = np.concatenate([[0.0], np.minimum(vt[1:] + latency, cfg.seconds)])
    b = simulate(replace(cfg, seed=seed_b), (shifted, v, act))
    return a, b


class Book:
    """Order book rebuilt from messages (by order id), for replay and for checking a feed."""

    def __init__(self):
        self.orders: dict[int, list] = {}          # oid -> [side, price, qty]
        self.levels = {1: {}, -1: {}}              # side -> price -> total qty

    def apply(self, m) -> None:
        kind, oid, side, px, qty = m["kind"], int(m["oid"]), int(m["side"]), int(m["price"]), int(m["qty"])
        lv = self.levels[side]
        if kind == b"A":
            self.orders[oid] = [side, px, qty]
            lv[px] = lv.get(px, 0) + qty
            return
        o = self.orders[oid]
        o[2] -= qty
        lv[px] -= qty
        if o[2] == 0:
            del self.orders[oid]
        if lv[px] == 0:
            del lv[px]

    def best(self) -> tuple[int, int, int, int]:
        b, a = self.levels[1], self.levels[-1]
        bb, ba = max(b), min(a)
        return bb, b[bb], ba, a[ba]

    def depth(self, side: int, n: int) -> list[tuple[int, int]]:
        lv = self.levels[side]
        return [(p, lv[p]) for p in sorted(lv, reverse=(side == 1))[:n]]
