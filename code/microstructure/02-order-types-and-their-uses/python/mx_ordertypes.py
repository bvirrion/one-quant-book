"""One Quant Book 10, chapter 2: order types on the exchange simulator.

    showcase()                      eight orders of different types sent to one book: what each one did
    stop_cascade(n_stops, ...)      a market sell into a bid ladder with sell stops beneath: how far the price falls
    iceberg_study(delay_ms, ...)    an iceberg refilled by the venue or by an algorithm after a random delay, and a
                                    refill detector run on the public feed: detection and false-alarm rates
    free_option(d, sigma, T)        the value of the option a resting limit order gives away (Bachelier)
    passive_markout(tape, h)        the mean loss of passive fills h seconds later in a firm.tape session
All deterministic (fixed seeds).
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("exchsim", "lob", "tape"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_exchsim import (  # noqa: E402
    SEC,
    Agent,
    ExchangeConfig,
    LatencyModel,
    Order,
    Phases,
    SessionSpec,
    Simulator,
    TapeBackground,
)
from firm_exchsim_codec import NT  # noqa: E402
from firm_exchsim_engine import Engine  # noqa: E402
from firm_lob import MessageBook  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402

C, IN = NT["ctl"], NT["in"]
OPEN = 34_200 * SEC


class _Run:
    """A bare engine with two logged-in firms and a continuous phase: the chapter's bench."""

    def __init__(self):
        self.e = Engine(ExchangeConfig().engine_config())
        self.t = OPEN
        for m in (C["S"]("O"), C["L"](1, 1, "Y"), C["L"](2, 2, "Y"), C["P"](0, "T", "OPEN")):
            self.go(0, m)

    def go(self, s, m):
        self.t += 1_000_000
        return self.e.process(self.t, s, m)

    def order(self, s, cl, side, qty, px, tif="D", disp="Y", po="N", dq=0, mq=0, stop=0):
        return self.go(s, IN["O"](cl, 1, side, qty, px, tif, disp, po, dq, mq, 0, "N", stop))


def _summary(feed, reps, session):
    mine = [r for s, r in reps if s == session]
    kinds = "".join(type(r).__name__[-1] for r in mine)
    filled = sum(r.qty for r in mine if type(r).__name__ == "Out_E")
    reason = next((r.reason for r in mine if type(r).__name__ in ("Out_C", "Out_J")), "")
    shown = sum(m.shares for m in feed if type(m).__name__ == "Feed_A")
    return {"reports": kinds, "filled": filled, "reason": reason, "displayed": shown}


def showcase() -> list[tuple[str, dict]]:
    """A book of 300 at 99.99 and 500 at 100.01 (firm 1); then firm 2 sends eight orders, one of each kind."""
    r = _Run()
    r.order(1, 1, "B", 300, 999_900)
    r.order(1, 2, "S", 500, 1_000_100)
    rows = []
    cases = [("limit buy 100 at 100.00 (rests)", dict(side="B", qty=100, px=1_000_000)),
             ("marketable limit buy 200 at 100.01", dict(side="B", qty=200, px=1_000_100)),
             ("post-only buy 100 at 100.01", dict(side="B", qty=100, px=1_000_100, po="Y")),
             ("fill-or-kill buy 400 at 100.01", dict(side="B", qty=400, px=1_000_100, tif="F")),
             ("immediate-or-cancel buy 400 at 100.01", dict(side="B", qty=400, px=1_000_100, tif="I")),
             ("iceberg sell 1,000 showing 100 at 100.02", dict(side="S", qty=1000, px=1_000_200, dq=100)),
             ("midpoint peg sell 200", dict(side="S", qty=200, px=0, disp="M")),
             ("sell stop 300 at 99.99", dict(side="S", qty=300, px=0, stop=999_900))]
    for k, (name, kw) in enumerate(cases, start=10):
        feed, reps = r.order(2, k, kw["side"], kw["qty"], kw["px"], kw.get("tif", "D"), kw.get("disp", "Y"),
                             kw.get("po", "N"), kw.get("dq", 0), 0, kw.get("stop", 0))
        rows.append((name, _summary(feed, reps, 2)))
    return rows


def stop_cascade(n_stops: int = 10, stop_qty: int = 800, market_qty: int = 3000, levels: int = 40,
                 depth: int = 500, limit_offset: int | None = None) -> dict:
    """A bid ladder of `depth` shares at every cent below 100.00; `n_stops` sell stops of `stop_qty` at every cent
    from 99.95 down; a market sell of `market_qty`. Returns the last trade price and the shares traded. With
    limit_offset (cents), the stops are stop-limit orders priced that far below their trigger."""
    r = _Run()
    cl = 1
    for k in range(levels):
        r.order(1, cl, "B", depth, 1_000_000 - 100 * k)
        cl += 1
    for k in range(n_stops):
        trig = 999_500 - 100 * k
        px = 0 if limit_offset is None else trig - 100 * limit_offset
        r.order(2, 1000 + k, "S", stop_qty, px, stop=trig)
    feed, reps = r.order(2, 5000, "S", market_qty, 0, tif="I")
    execs = [x for x in feed if type(x).__name__ == "Feed_E"]
    last = r.e.inst[1].last
    return {"last": last, "drop_cents": (1_000_000 - last) // 100, "traded": sum(x.shares for x in execs),
            "stops_triggered": len({x.cl_ord_id for s, x in reps if s == 2 and type(x).__name__ == "Out_E"
                                    and 1000 <= x.cl_ord_id < 5000})}


class _Iceberg(Agent):
    """Sells `total` shares showing `show` at a time at the best ask. mode 'venue': one iceberg order (the venue
    refreshes it); mode 'algo': the agent sends a new displayed order after each slice fills, after a random delay
    and with a size drawn uniformly within +-jitter of `show`."""

    name = "iceberg"

    def __init__(self, mode: str, show: int = 300, total: int = 30_000, delay_ms: float = 0.0, jitter: float = 0.0,
                 seed: int = 1, follow: bool = False):
        self.mode, self.show, self.left, self.delay, self.jitter = mode, show, total, delay_ms, jitter
        self.follow = follow
        self.rng = np.random.default_rng(seed)
        self.price, self.live = None, None

    def on_book(self, ctx, loc, top):
        if self.price is None and top[2] is not None and ctx.now_ns > OPEN + 5 * SEC:
            self.price = top[2]
            if self.mode == "venue":
                ctx.send(Order(1, "S", self.left, self.price, display_qty=self.show))
            else:
                self._slice(ctx)

    def _slice(self, ctx):
        if self.left <= 0:
            return
        size = self.show
        if self.jitter:
            size = int(round(self.show * (1 + self.jitter * (2 * self.rng.random() - 1)) / 100.0)) * 100
        size = max(100, min(size, self.left))
        self.left -= size
        if self.follow and ctx.top(1)[2] is not None:
            self.price = ctx.top(1)[2]
        self.live = ctx.send(Order(1, "S", size, self.price))

    def on_report(self, ctx, rep):
        if self.mode == "algo" and type(rep).__name__ == "Out_E" and rep.leaves == 0:
            ctx.set_timer(int(self.rng.exponential(self.delay * 1e6)) if self.delay else 0, "refill")

    def on_timer(self, ctx, tag):
        self._slice(ctx)


def iceberg_study(mode: str = "algo", delay_ms: float = 0.0, jitter: float = 0.0, window_ms: float = 50.0,
                  tol: float = 0.0, seconds: float = 1800.0, seed: int = 11, follow: bool = False) -> dict:
    """Run the iceberg in a simulated half hour; detect refills on the public feed: after an execution that removes
    a displayed order entirely, an add on the same side and price within `window_ms` whose size is within `tol`
    (relative) of the removed order's original size. Returns true refills, detections and false alarms."""
    end = OPEN + int(seconds * SEC)
    ph = Phases(start_ns=OPEN - SEC, open_ns=OPEN, close_ns=end, end_ns=end + 1)
    sim = Simulator(ExchangeConfig(phases=ph), seed=seed)
    sim.add_background(TapeBackground(TapeConfig(seconds=seconds, seed=seed, news_at=None)))
    agent = _Iceberg(mode, delay_ms=delay_ms, jitter=jitter, seed=seed, follow=follow)
    sim.add_agent(agent, SessionSpec(firm="ICE", latency=LatencyModel(50_000, 50_000, 50_000)))
    res = sim.run()
    ice_refs = {r.ref for r in res.sim.venues[0].reports.get(res.sim.by_name["iceberg@SIMX"].sid, [])
                if type(r).__name__ == "Out_A"}
    book = MessageBook()
    orig: dict[int, int] = {}
    pending: list[tuple[int, int, int, int]] = []       # (deadline, side, price, size) after a full execution
    ice_adds = detections = false_alarms = 0
    last_ice_exec = None                                # (ts, price) of the latest execution of an iceberg slice
    for ts, _, m in res.feed_messages():
        k = type(m).__name__[-1]
        if k == "A":
            side = 1 if m.side == "B" else -1
            if mode == "venue" and last_ice_exec == (ts, m.price) and side == -1:
                ice_refs.add(m.ref)                     # the venue's refresh: same event, new reference
            is_ice = m.ref in ice_refs
            ice_adds += is_ice
            if any(dl >= ts and sd == side and px == m.price and abs(m.shares - q) <= tol * q
                   for dl, sd, px, q in pending):
                detections += is_ice
                false_alarms += not is_ice
            book.apply("A", m.ref, side, m.price, m.shares)
            orig[m.ref] = m.shares
        elif k in "EXC":
            o = book.book.get(m.ref)
            if k == "E" and m.ref in ice_refs:
                last_ice_exec = (ts, o.price)
            if k == "E" and o.qty == m.shares:
                pending.append((ts + int(window_ms * 1e6), o.side, o.price, orig[m.ref]))
            book.apply("X", m.ref, qty=m.shares)
        elif k == "D":
            book.apply("D", m.ref)
        elif k == "U":
            book.apply("U", m.ref, price=m.price, qty=m.shares, new_ref=m.new_ref)
            orig[m.new_ref] = m.shares
        pending = [q for q in pending if q[0] >= ts]
    true_refills = max(ice_adds - 1, 0)
    return {"refills": true_refills, "detected": detections, "false_alarms": false_alarms,
            "rate": detections / true_refills if true_refills else math.nan,
            "fills": len(res.agents["iceberg"].fills), "sold": int(sum(f[5] for f in res.agents["iceberg"].fills))}


def free_option(d: float, sigma: float, horizon: float) -> float:
    """Expected loss of a resting sell at distance d above the efficient price, picked off at the horizon: the
    Bachelier call value sigma sqrt(T) phi(d / sigma sqrt(T)) - d (1 - Phi(d / sigma sqrt(T)))."""
    s = sigma * math.sqrt(horizon)
    z = d / s
    phi = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)
    big = 0.5 * math.erfc(z / math.sqrt(2))
    return s * phi - d * big


def passive_markout(tape, horizon: float = 10.0) -> dict:
    """Mean gain, in ticks per share, of the passive side of every trade, marked to the efficient price `horizon`
    seconds later; split by informed and uninformed aggressors."""
    t, v = tape.v_t, tape.v
    tr = tape.trades
    idx = np.searchsorted(t, tr["t"] + horizon, side="right") - 1
    later = v[np.clip(idx, 0, len(v) - 1)]
    gain = -tr["sign"] * (later - tr["price"])            # the passive side sold if the aggressor bought
    w = tr["qty"]
    inf = tr["informed"]
    return {"all": float(np.average(gain, weights=w)), "informed": float(np.average(gain[inf], weights=w[inf])),
            "uninformed": float(np.average(gain[~inf], weights=w[~inf])),
            "informed_share": float(w[inf].sum() / w.sum())}


def sigma_per_sqrt_second(tape) -> float:
    """Volatility of the efficient price, in ticks per square-root second."""
    dv = np.diff(tape.v)
    return float(math.sqrt((dv**2).sum() / tape.cfg.seconds))


def session(seconds: float = 3600.0, seed: int = 7):
    return simulate(TapeConfig(seconds=seconds, seed=seed))
