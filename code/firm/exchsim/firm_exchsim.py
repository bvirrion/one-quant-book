"""firm.exchsim -- the exchange simulator (build of One Quant Book 10, chapter 26; contract: INTERFACES.md section 7).

One or more venues, each a deterministic matching engine (firm_exchsim_engine.Engine) behind a simulated network:
agents send orders through order-entry sessions with latency, see the market through a sequenced feed with
latency, and receive execution reports; background flow (Book 7's firm_tape, replayed as real orders) or an
agent population (firm.agentmkt) makes the market. Time is integer nanoseconds since midnight, prices integers
in 1/10,000 currency unit. Same configuration, seed and inputs give byte-identical feeds and reports.

API (stable; see PROTOCOL.md for the wire formats and STATUS.md for what has landed):
    InstrumentSpec, FeeSchedule, Phases, Throttle, FeedConfig, Fault, ExchangeConfig   venue configuration
    LatencyModel, SessionSpec, Order                                                    participants
    Simulator(venues, inter_venue_ns=None, sip=None, seed=1)      sip=SipConfig(...) adds a consolidated feed:
                                                    Result.sip(locate), Agent.on_nbbo, ctx.nbbo(), ctx.direct_nbbo()
        .add_background(TapeBackground(...))        background flow (reactive to the book: real orders)
        .add_agent(agent, spec | [specs]) -> name   an Agent (on_start, on_feed, on_book, on_report, on_timer)
        .add_events(jumps=(), orders=(), controls=())   efficient-price jumps (ticks), scripted orders, controls
        .schedule_call(t_ns, fn, *args)             fn(t_ns, *args) at that time, among the controls (venue-side
                                                    processes: firm.halts policies)
        .run(until_ns=None) -> Result
    Result: sip(locate), feed_bytes(venue, line), snapshot_bytes(venue), retransmit(venue, seq, count),
        recorded(venue, line), tape(venue, locate), reports(firm), drop_copy(firm), journal, journal_bytes(venue),
        truth, agents, engine(venue), feed_messages(venue)
    Agent (base class) and ctx: now_ns, send(Order) -> cl_ord_id, replace, cancel, mass_cancel, quote, set_timer,
        book(locate), position(locate), cash, working() (with the quantity ahead in queue), compute(ns), top(locate)
    TapeAgentAdapter(agent), ReplayStrategyAdapter(strategy)     Book 7 agents and replay strategies, unchanged
    presets: us_equity_lit(), pro_rata_futures(), midpoint_dark_pool(), speed_bumped(), periodic_batch(),
        auction_venue(), crypto_venue()
    rng_u64(seed, stream, n), rng_uniform(...), rng_normal(...)  the counter-based SplitMix64 streams
"""
from __future__ import annotations

import heapq
import math
import pathlib
import sys
from collections import deque
from dataclasses import dataclass, field, replace

import numpy as np

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
for _c in ("lob", "tape", "nbbo"):
    sys.path.insert(0, str(_HERE.parent / _c))
from firm_exchsim_codec import (  # noqa: E402
    NT,
    encode,
    file_record,
    journal_record,
    mold_end,
    mold_packet,
)
from firm_exchsim_engine import Engine  # noqa: E402
from firm_lob import MessageBook  # noqa: E402

CTL, IN, FEED, OUT = NT["ctl"], NT["in"], NT["feed"], NT["out"]
SEC = 1_000_000_000
OPEN_NS, CLOSE_NS = 34_200 * SEC, 57_600 * SEC           # 09:30 and 16:00
MASK = (1 << 64) - 1

# ---------------------------------------------------------------------------------------------------------------
# counter-based randomness (identical in the C++20 server): the n-th output of SplitMix64 seeded with a stream key


def _mix(z: int) -> int:
    z = (z + 0x9E3779B97F4A7C15) & MASK
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
    return z ^ (z >> 31)


def stream_key(seed: int, *parts: int) -> int:
    k = _mix(seed & MASK)
    for p in parts:
        k = _mix(k ^ (p & MASK))
    return k


def rng_u64(key: int, n: int) -> int:
    return _mix((key + n * 0x9E3779B97F4A7C15) & MASK)


def rng_uniform(key: int, n: int) -> float:
    return (rng_u64(key, n) >> 11) * (1.0 / 9007199254740992.0)


def rng_normal(key: int, n: int) -> float:
    u1 = max(rng_uniform(key, 2 * n), 1e-300)
    u2 = rng_uniform(key, 2 * n + 1)
    return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)


# ---------------------------------------------------------------------------------------------------------------
# configuration


@dataclass(frozen=True)
class InstrumentSpec:
    symbol: str = "SIM1"
    locate: int = 1
    tick: int = 100                         # 0.01 in 1/10,000 units
    lot: int = 100
    start_price: int = 1_000_000            # 100.00
    matching: str = "fifo"                  # 'fifo' | 'pro_rata' | 'configurable'
    alloc: dict | None = None               # top_pct, fifo_pct, min_alloc (pro rata and configurable)
    band: float = 0.0                       # static collar as a fraction of start_price (0 = none)


@dataclass(frozen=True)
class FeeSchedule:
    make: float = -0.0020                   # currency per share (unit 'share') or basis points (unit 'bp')
    take: float = 0.0030
    cross: float = 0.0
    unit: str = "share"
    tiers: tuple = ()                       # monthly tiers are billed after the fact (Book 1's firm.feesched)

    def micro(self) -> dict:
        k = 1_000_000 if self.unit == "share" else 100      # 1e-6 currency per share, or 1e-2 bp (1e-6 of notional)
        return {"unit": self.unit, "make": round(self.make * k), "take": round(self.take * k),
                "cross": round(self.cross * k)}


@dataclass(frozen=True)
class Phases:
    start_ns: int = OPEN_NS - 60 * SEC      # start of messages
    open_ns: int = OPEN_NS
    close_ns: int = CLOSE_NS
    end_ns: int = CLOSE_NS + 60 * SEC
    open_auction: bool = False
    preopen_ns: int | None = None           # opening call starts (default: open - 5 minutes)
    close_auction: bool = False
    close_call_ns: int | None = None        # a closing call phase (continuous trading stops); None: cross at close
    moc_cutoff_ns: int | None = None        # at-the-close entry frozen from here
    indicative_every_ns: int = 0            # indicative price and imbalance publication during calls
    random_end_ns: int = 0                  # uncross at a uniform random time in [t, t + random_end_ns)


@dataclass(frozen=True)
class Throttle:
    rate: int = 0                           # messages (weight units) per second; 0 = none
    burst: int = 0
    weights: tuple = ()                     # ((message type, weight), ...): a request-weight rate limit


@dataclass(frozen=True)
class FeedConfig:
    lines: tuple = ("A", "B")
    loss: float = 0.0                       # independent packet loss per line
    burst_loss: tuple | None = None         # Gilbert-Elliott (p_good_to_bad, p_bad_to_good, loss_in_bad)
    dup: float = 0.0
    reorder_window: int = 0                 # 0: each line stays in order; >0: jitter may reorder
    jitter_ns: int = 0                      # exponential extra delay per packet (mean)
    line_ns: tuple = (0, 0)                 # fixed extra delay of line A and line B
    outages: tuple = ()                     # ((line, start_ns, end_ns), ...)
    snapshot_every_ns: int = 0
    heartbeat_ns: int = SEC
    max_packet: int = 1400
    window: int = 100_000                   # retransmission window (messages)
    max_retransmit: int = 1000              # messages per request


@dataclass(frozen=True)
class Fault:
    kind: str                               # 'drop_session' | 'refuse_login' | 'pause' | 'halt'
    start_ns: int
    end_ns: int = 0
    session: str = ""                       # the session's name (drop_session, refuse_login)
    locate: int = 0                         # halt: 0 = all instruments
    call_ns: int = 0                        # halt: reopening call before trading resumes


@dataclass(frozen=True)
class ExchangeConfig:
    venue: str = "SIMX"
    instruments: tuple = (InstrumentSpec(),)
    fees: FeeSchedule = FeeSchedule()
    phases: Phases = Phases()
    halts: object = None                    # firm.halts policy (bands, pauses), or None
    throttle: Throttle = Throttle()
    engine_ns: int = 500
    speed_bump_ns: int = 0
    asymmetric_delay: bool = False          # the bump spares cancels, mass cancels and post-only orders
    batch_interval_ns: int = 0              # > 0: frequent batch auctions instead of continuous trading
    feed: FeedConfig = FeedConfig()
    faults: tuple = ()
    seed: int = 1
    session: str = ""                       # MoldUDP64 session name (default: venue padded)
    reference: str = ""                     # a dark venue: the lit venue whose top of book prices its midpoint
    reference_ns: int = 0                   #   pegs (control N, sent reference_ns after each change of that top)

    def engine_config(self) -> dict:
        m = {"fifo": "F", "pro_rata": "P", "configurable": "C"}
        inst = []
        for i in self.instruments:
            a = dict(i.alloc or {})
            if i.matching == "pro_rata":
                a.setdefault("top_pct", 0)
                a.setdefault("fifo_pct", 0)
            inst.append({"locate": i.locate, "symbol": i.symbol, "tick": i.tick, "lot": i.lot,
                         "matching": m[i.matching], "top_pct": a.get("top_pct", 0),
                         "fifo_pct": a.get("fifo_pct", 0), "min_alloc": a.get("min_alloc", 1),
                         "start_price": i.start_price})
        th = {"rate": self.throttle.rate, "burst": self.throttle.burst}
        if self.throttle.weights:
            th["weights"] = dict(self.throttle.weights)
        return {"venue": self.venue, "session": self.mold_session, "engine_ns": self.engine_ns,
                "fees": self.fees.micro(), "throttle": th, "instruments": inst}

    @property
    def mold_session(self) -> str:
        return (self.session or self.venue)[:10].ljust(10)


@dataclass(frozen=True)
class LatencyModel:
    entry_ns: int = 20_000
    ack_ns: int = 20_000
    data_ns: int = 20_000
    jitter: float = 0.0                     # lognormal sigma of a multiplicative factor with mean one
    spike_prob: float = 0.0
    spike_ns: int = 0


@dataclass(frozen=True)
class SessionSpec:
    firm: str = "AGENT"
    venue: str = ""                         # default: the simulator's first venue
    latency: LatencyModel = LatencyModel()
    cod: bool = True
    stp_group: int = 0
    drop_copy: bool = False
    name: str = ""


@dataclass(frozen=True)
class SipConfig:
    """A consolidated feed (securities information processor): each venue's top of book reaches it after
    venue_ns[venue] (default_ns otherwise), it computes the national best bid and offer with Book 1's firm_nbbo
    (quotes of at least round_lot shares only) and publishes each change process_ns later; agents receive it
    agent_ns after publication (Agent.on_nbbo) and read the last one with ctx.nbbo(locate)."""
    default_ns: int = 500_000
    venue_ns: dict = field(default_factory=dict)
    process_ns: int = 20_000
    agent_ns: int = 20_000
    round_lot: int = 100


@dataclass
class Order:
    locate: int = 1
    side: str = "B"
    qty: int = 100
    price: int = 0                          # 0 = market
    tif: str = "D"
    display: str = "Y"
    post_only: bool = False
    display_qty: int = 0
    min_qty: int = 0
    stp_group: int = 0
    stp_mode: str = "N"
    stop_price: int = 0
    cl_ord_id: int | None = None
    venue: str = ""


# ---------------------------------------------------------------------------------------------------------------
# agents


class Agent:
    """Override what you need. Callbacks run at the agent's own time (after its latencies and compute time)."""

    name = "agent"

    def on_start(self, ctx) -> None:
        pass

    def on_feed(self, ctx, msg) -> None:
        pass

    def on_book(self, ctx, locate: int, top) -> None:
        pass

    def on_report(self, ctx, rep) -> None:
        pass

    def on_timer(self, ctx, tag) -> None:
        pass

    def on_nbbo(self, ctx, locate: int, nbbo) -> None:
        """A consolidated-feed update (Simulator(sip=SipConfig(...)) only): nbbo is a firm_nbbo.Nbbo or None."""
        pass


@dataclass
class _Sess:
    sid: int
    name: str
    firm: str
    firm_id: int
    venue: int
    spec: SessionSpec
    key: int
    n_entry: int = 0
    n_ack: int = 0
    n_data: int = 0
    last_entry: int = 0
    last_ack: int = 0
    last_data: int = 0
    next_cl: int = 1


class Ctx:
    """The agent's handle on the market: everything it knows arrived through its sessions."""

    def __init__(self, sim, agent, sessions):
        self._sim, self.agent, self.sessions = sim, agent, sessions
        self.now_ns = 0
        self._busy = 0
        self._compute = 0
        self._out: list = []
        self.orders: dict[tuple[int, int], dict] = {}          # (session id, cl) -> state
        self._pos: dict[tuple[int, int], int] = {}             # (venue, locate) -> position
        self.cash = 0.0                                        # currency, fees included
        self.fees = 0.0
        self.books: dict[tuple[int, int], MessageBook] = {}
        self._tops: dict[tuple[int, int], tuple] = {}
        self.fills: list = []
        self._quote_id = 1 << 40                               # quote legs 2q, 2q+1 never meet sequential ids
        self._ahead_cache = None
        self._nbbo: dict[int, object] = {}                     # locate -> last consolidated-feed NBBO

    def nbbo(self, locate: int = 1):
        """The last NBBO received from the consolidated feed (None before the first, or without a SIP)."""
        return self._nbbo.get(locate)

    def direct_nbbo(self, locate: int = 1) -> tuple:
        """(best bid, bid size, best ask, ask size) across this agent's venues, from its own direct feeds."""
        bids, asks = [], []
        for (_vi, loc), bk in self.books.items():
            if loc != locate:
                continue
            b, bq, a, aq = bk.top()
            if b is not None:
                bids.append((b, bq))
            if a is not None:
                asks.append((a, aq))
        bb = max((b for b, _ in bids), default=None)
        ba = min((a for a, _ in asks), default=None)
        return (bb, sum(q for b, q in bids if b == bb), ba, sum(q for a, q in asks if a == ba))

    # -- helpers -----------------------------------------------------------------------------------------------
    def _session(self, venue: str | int | None) -> _Sess:
        if venue in (None, ""):
            return self.sessions[0]
        v = self._sim._venue_index(venue) if isinstance(venue, str) else venue
        for s in self.sessions:
            if s.venue == v:
                return s
        raise KeyError(f"no session at venue {venue}")

    def compute(self, ns: int) -> None:
        """Declare decision time: this callback's sends leave `ns` later, and the agent is busy until then."""
        self._compute += int(ns)

    def send(self, order: Order) -> int:
        s = self._session(order.venue)
        cl = order.cl_ord_id if order.cl_ord_id is not None else s.next_cl
        s.next_cl = max(s.next_cl, cl + 1)
        msg = IN["O"](cl, order.locate, order.side, order.qty, order.price, order.tif, order.display,
                      "Y" if order.post_only else "N", order.display_qty, order.min_qty, order.stp_group,
                      order.stp_mode, order.stop_price)
        self.orders[(s.sid, cl)] = {"cl": cl, "session": s.sid, "venue": s.venue, "locate": order.locate,
                                    "side": order.side, "price": order.price, "qty": order.qty,
                                    "leaves": order.qty, "ref": None, "status": "pending", "display": order.display}
        self._out.append((s, msg))
        return cl

    def replace(self, cl: int, qty: int, price: int, venue=None) -> int:
        s = self._session(venue)
        new = s.next_cl
        s.next_cl += 1
        self._out.append((s, IN["U"](cl, new, qty, price)))
        return new

    def cancel(self, cl: int, leave_qty: int = 0, venue=None) -> None:
        s = self._session(venue)
        self._out.append((s, IN["X"](cl, leave_qty)))

    def mass_cancel(self, locate: int = 0, side: str = "*", venue=None) -> None:
        s = self._session(venue)
        self._out.append((s, IN["M"](locate, side)))

    def quote(self, locate: int, bid_price: int, bid_qty: int, ask_price: int, ask_qty: int, venue=None) -> int:
        """A two-sided mass quote replacing this session's previous one on `locate`; legs are cl 2q and 2q+1."""
        s = self._session(venue)
        q = self._quote_id
        self._quote_id += 1
        for cl, side, px, qty in ((2 * q, "B", bid_price, bid_qty), (2 * q + 1, "S", ask_price, ask_qty)):
            if qty:
                self.orders[(s.sid, cl)] = {"cl": cl, "session": s.sid, "venue": s.venue, "locate": locate,
                                            "side": side, "price": px, "qty": qty, "leaves": qty, "ref": None,
                                            "status": "pending", "display": "Y"}
        self._out.append((s, IN["Q"](q, locate, bid_price, bid_qty, ask_price, ask_qty)))
        return q

    def set_timer(self, delay_ns: int, tag=None) -> None:
        self._sim._push(self.now_ns + self._compute + int(delay_ns), 3, ("timer", self, tag))

    def book(self, locate: int = 1, venue=None) -> MessageBook:
        v = self._session(venue).venue
        return self.books.setdefault((v, locate), MessageBook())

    def top(self, locate: int = 1, venue=None):
        return self.book(locate, venue).top()

    def position(self, locate: int = 1, venue=None) -> int:
        return self._pos.get((self._session(venue).venue, locate), 0)

    def working(self) -> list[dict]:
        """Live orders with the displayed quantity ahead of each in this agent's view of the queue."""
        out = []
        for o in self.orders.values():
            if o["status"] not in ("live", "pending"):
                continue
            d = dict(o)
            d["ahead"] = None
            if o["ref"] is not None and o["display"] == "Y":
                bk = self.books.get((o["venue"], o["locate"]))
                if bk is not None:
                    side = 1 if o["side"] == "B" else -1
                    ahead = 0
                    for x in bk.book.level_orders(side, o["price"]):
                        if x.ref == o["ref"]:
                            break
                        ahead += x.qty
                    d["ahead"] = ahead
            out.append(d)
        return out

    # -- updates from reports ------------------------------------------------------------------------------------
    def _on_report(self, s: _Sess, rep) -> None:
        t = type(rep).__name__[-1]
        key = (s.sid, getattr(rep, "cl_ord_id", 0))
        o = self.orders.get(key)
        if t == "A" and o is not None:
            o["ref"], o["status"] = rep.ref, "live"
        elif t == "E" and o is not None:
            o["leaves"] = rep.leaves
            if rep.leaves == 0:
                o["status"] = "filled"
            sign = 1 if o["side"] == "B" else -1
            k = (s.venue, o["locate"])
            self._pos[k] = self._pos.get(k, 0) + sign * rep.qty
            self.cash -= sign * rep.qty * rep.price / 10_000.0
            self.cash -= rep.fee / 1_000_000.0
            self.fees += rep.fee / 1_000_000.0
            self.fills.append((rep.ts, s.venue, o["locate"], sign, rep.price, rep.qty, rep.liquidity, rep.fee))
        elif t == "C" and o is not None:
            o["leaves"] = max(0, o["leaves"] - rep.decrement)
            if o["leaves"] == 0:
                o["status"] = "cancelled"
        elif t == "J" and o is not None:
            o["status"] = "rejected"
        elif t == "U":
            old = self.orders.pop((s.sid, rep.cl_ord_id), None)
            if old is not None:
                old = dict(old, cl=rep.new_cl_ord_id, ref=rep.ref, qty=rep.qty, leaves=rep.qty, price=rep.price,
                           status="live")
                self.orders[(s.sid, rep.new_cl_ord_id)] = old
        elif t == "J" and o is None:
            pass


# ---------------------------------------------------------------------------------------------------------------
# background flow


@dataclass
class TapeBackground:
    """Book 7's firm_tape session replayed as real orders: its adds as day limit orders, its cancellations as
    cancels, each of its trades as one market order of the trade's total size on the aggressor's side. Orders
    meet whatever the book holds when they arrive, so agents' orders change what the background executes
    against (the reactive replacement for shadow-order replay, INTERFACES.md section 4)."""

    cfg: object = None                      # firm_tape.TapeConfig
    venue: str = ""
    locate: int = 1
    start_ns: int = OPEN_NS
    name: str = "BG"
    v_path: object = None                   # an imposed efficient path (times s, ticks[, activity]), as
                                            # firm_tape.simulate takes it: several venues on one price

    def build(self, sim, venue_cfg: ExchangeConfig, jumps=()):
        from firm_tape import TapeConfig, activity, efficient_path, simulate
        cfg = self.cfg or TapeConfig()
        inst = next(i for i in venue_cfg.instruments if i.locate == self.locate)
        k = inst.tick
        v_path = self.v_path
        if jumps:
            rng = np.random.default_rng(cfg.seed)
            act = activity(cfg, rng)
            vt, v = efficient_path(cfg, rng, act)
            vt, v = list(vt), list(v)
            for t_ns, size in sorted(jumps):
                ts = (t_ns - self.start_ns) / SEC
                i = int(np.searchsorted(vt, ts, side="right"))
                base = v[i - 1]
                vt.insert(i, ts)
                v.insert(i, base + size)
                for j in range(i + 1, len(v)):
                    v[j] += size
            v_path = (np.array(vt), np.array(v), act)
        tape = simulate(cfg, v_path)
        recs, informed = [], {}
        trade_rows = {int(r["trade"]): r for r in tape.trades}
        seen_trade = set()
        for m in tape.msgs:
            t_ns = self.start_ns + round(float(m["t"]) * SEC)
            kind = m["kind"]
            if kind == b"A":
                recs.append((t_ns, IN["O"](int(m["oid"]), self.locate, "B" if m["side"] == 1 else "S", int(m["qty"]),
                                           int(m["price"]) * k, "D", "Y", "N", 0, 0, 0, "N", 0)))
            elif kind == b"X":
                recs.append((t_ns, IN["X"](int(m["oid"]), 0)))
            else:
                tid = int(m["trade"])
                if tid in seen_trade:
                    continue
                seen_trade.add(tid)
                row = trade_rows[tid]
                cl = 10**12 + tid
                informed[cl] = bool(row["informed"])
                recs.append((t_ns, (tid, cl, int(m["agg"]))))
        # trade sizes: the sum of the executions carrying each trade id
        sizes: dict[int, int] = {}
        for m in tape.msgs[tape.msgs["kind"] == b"E"]:
            sizes[int(m["trade"])] = sizes.get(int(m["trade"]), 0) + int(m["qty"])
        out = []
        for t_ns, x in recs:
            if isinstance(x, tuple) and not hasattr(x, "_fields"):
                tid, cl, agg = x
                x = IN["O"](cl, self.locate, "B" if agg == 1 else "S", sizes[tid], 0, "I", "Y", "N", 0, 0, 0, "N", 0)
            out.append((t_ns, x))
        truth = {"v_t": self.start_ns + np.round(tape.v_t * SEC).astype(np.int64), "v": tape.v * k,
                 "informed": informed, "tape_cfg": cfg}
        return out, truth


# ---------------------------------------------------------------------------------------------------------------
# the simulator


class _Venue:
    def __init__(self, idx: int, cfg: ExchangeConfig):
        self.idx, self.cfg = idx, cfg
        self.engine = Engine(cfg.engine_config())
        self.journal: list = []                  # (t_ns, session, msg)
        self.feed_log: list = []                 # (ts, first_seq, msgs)
        self.feed_seq = 0
        self.snaps: list = []                    # (t_ns, locate, msgs)
        self.reports: dict[int, list] = {}
        self.pause: list = [(f.start_ns, f.end_ns) for f in cfg.faults if f.kind == "pause"]
        self.bump = cfg.speed_bump_ns
        self._ref: dict[int, tuple] = {}         # locate -> last reference quote sent (dark venues)


class Simulator:
    def __init__(self, venues=None, inter_venue_ns=None, sip=None, seed: int = 1):
        if venues is None:
            venues = [ExchangeConfig()]
        if isinstance(venues, ExchangeConfig):
            venues = [venues]
        self.venues = [_Venue(i, v) for i, v in enumerate(venues)]
        self._dark_of: dict[str, list] = {}                     # lit venue -> dark venues it prices
        for w in self.venues:
            if w.cfg.reference:
                self._dark_of.setdefault(w.cfg.reference, []).append(w)
        self.inter_venue_ns = inter_venue_ns or {}
        self.sip, self.seed = sip, seed
        self._sip_tops: dict[tuple[int, int], tuple] = {}      # (venue, locate) -> last top sent to the SIP
        self._sip_nbbo: dict[int, object] = {}                 # locate -> firm_nbbo.NbboBuilder
        self.sip_log: list = []                                # (publish ns, locate, Nbbo or None)
        self.sessions: dict[tuple[int, int], _Sess] = {}      # (venue, sid) -> session
        self.by_name: dict[str, _Sess] = {}
        self.agents: list[tuple[Agent, Ctx]] = []
        self.backgrounds: list = []
        self._jumps: list = []
        self._scripted: list = []
        self._controls: list = []
        self._heap: list = []
        self._seq = 0
        self._firms: dict[str, int] = {}
        self._bg_sessions: set[tuple[int, int]] = set()
        self.truth: dict = {"v_t": np.zeros(0, np.int64), "v": np.zeros(0), "informed": {}}
        self._streams: dict = {}

    # -- setup ---------------------------------------------------------------------------------------------------
    def _venue_index(self, name: str) -> int:
        if not name:
            return 0
        for v in self.venues:
            if v.cfg.venue == name:
                return v.idx
        raise KeyError(name)

    def _firm_id(self, firm: str) -> int:
        return self._firms.setdefault(firm, len(self._firms) + 1)

    def _new_session(self, spec: SessionSpec, name: str) -> _Sess:
        v = self._venue_index(spec.venue)
        sid = 1 + sum(1 for (vv, _) in self.sessions if vv == v)
        s = _Sess(sid, name, spec.firm, self._firm_id(spec.firm), v, spec, stream_key(self.seed, v, sid))
        self.sessions[(v, sid)] = s
        self.by_name[name] = s
        return s

    def add_background(self, bg) -> None:
        name = bg.name if bg.name not in self.by_name else f"{bg.name}{len(self.backgrounds) + 1}"
        s = self._new_session(SessionSpec(firm="BACKGROUND", venue=bg.venue, cod=False, name=name), name)
        self._bg_sessions.add((s.venue, s.sid))
        self.backgrounds.append((bg, s))

    def add_agent(self, agent: Agent, spec=None) -> str:
        specs = spec if isinstance(spec, (list, tuple)) else [spec or SessionSpec()]
        base = getattr(agent, "name", "agent") or "agent"
        name = base if base not in {n.split("@")[0] for n in self.by_name} else f"{base}{len(self.agents) + 1}"
        sess = [self._new_session(sp, f"{name}@{self.venues[self._venue_index(sp.venue)].cfg.venue}")
                for sp in specs]
        ctx = Ctx(self, agent, sess)
        self.agents.append((agent, ctx))
        for s in sess:
            self._streams[(id(ctx), s.venue, "data")] = deque()
        return name

    def schedule_call(self, t_ns: int, fn, *args) -> None:
        """Call fn(t_ns, *args) at simulated time t_ns, among the venue's controls (a venue-side process such as a
        firm.halts policy that watches the book and sends controls)."""
        self._push(int(t_ns), 0, ("call", fn) + tuple(args))

    def add_events(self, jumps=(), orders=(), controls=()) -> None:
        """jumps: (t_ns, ticks) moves of the background's efficient price; orders: (t_ns, venue, Order or a raw
        In_* message) sent by a scripted session per venue (arriving at t_ns); controls: (t_ns, venue, Ctl_*)."""
        self._jumps += list(jumps)
        self._scripted += list(orders)
        self._controls += list(controls)

    def _push(self, t: int, cls: int, payload) -> None:
        heapq.heappush(self._heap, (t, cls, self._seq, payload))
        self._seq += 1

    # -- latency ---------------------------------------------------------------------------------------------------
    def _lat(self, s: _Sess, direction: int) -> int:
        lm = s.spec.latency
        base = (lm.entry_ns, lm.ack_ns, lm.data_ns)[direction]
        n = (s.n_entry, s.n_ack, s.n_data)[direction]
        if direction == 0:
            s.n_entry += 1
        elif direction == 1:
            s.n_ack += 1
        else:
            s.n_data += 1
        key = s.key ^ (direction + 1)
        x = base
        if lm.jitter > 0:
            x = base * math.exp(lm.jitter * rng_normal(key, n) - 0.5 * lm.jitter**2)
        if lm.spike_prob > 0 and rng_uniform(key ^ 0x5B, n) < lm.spike_prob:
            x += lm.spike_ns
        return int(round(x))

    # -- controls --------------------------------------------------------------------------------------------------
    def _schedule_controls(self, v: _Venue) -> None:
        cfg, ph = v.cfg, v.cfg.phases
        key = stream_key(self.seed, v.idx, 0xAC)
        push = self._push

        def ctl(t, m):
            push(t, 0, ("ctl", v, m))
        ctl(ph.start_ns, CTL["S"]("O"))
        for (vi, sid), s in sorted(self.sessions.items()):
            if vi == v.idx:
                ctl(ph.start_ns, CTL["L"](sid, s.firm_id, "Y" if s.spec.cod else "N"))
        for i in cfg.instruments:
            if i.band:
                lo = int(i.start_price * (1 - i.band)) // i.tick * i.tick
                hi = -(-int(i.start_price * (1 + i.band)) // i.tick) * i.tick
                ctl(ph.start_ns, CTL["R"](i.locate, i.start_price, lo, hi))
        ctl(ph.start_ns, CTL["S"]("S"))
        t_open = ph.open_ns
        if ph.random_end_ns:
            t_open_end = ph.open_ns + int(rng_uniform(key, 0) * ph.random_end_ns)
        else:
            t_open_end = ph.open_ns
        if ph.open_auction:
            pre = ph.preopen_ns if ph.preopen_ns is not None else ph.open_ns - 300 * SEC
            ctl(pre, CTL["P"](0, "O", "PREO"))
            if ph.indicative_every_ns:
                t = pre + ph.indicative_every_ns
                while t < t_open_end:
                    ctl(t, CTL["I"](0, "O"))
                    t += ph.indicative_every_ns
            t_open = t_open_end
        ctl(t_open, CTL["S"]("Q"))
        if cfg.batch_interval_ns:
            ctl(t_open, CTL["P"](0, "B", "FBA "))
            t = t_open + cfg.batch_interval_ns
            while t < ph.close_ns:
                ctl(t, CTL["X"](0, "B"))
                t += cfg.batch_interval_ns
        else:
            ctl(t_open, CTL["P"](0, "T", "OPEN"))
        if ph.moc_cutoff_ns is not None:
            ctl(ph.moc_cutoff_ns, CTL["F"](0, "Y"))
        t_close = ph.close_ns + (int(rng_uniform(key, 1) * ph.random_end_ns) if ph.random_end_ns else 0)
        call0 = ph.close_call_ns if ph.close_call_ns is not None else ph.moc_cutoff_ns
        if ph.close_call_ns is not None:
            ctl(ph.close_call_ns, CTL["P"](0, "K", "CLCA"))
        if ph.close_auction and ph.indicative_every_ns and call0 is not None:
            t = call0 + ph.indicative_every_ns
            while t < t_close:
                ctl(t, CTL["I"](0, "C"))
                t += ph.indicative_every_ns
        ctl(t_close, CTL["P"](0, "C", "CLOS"))
        ctl(t_close, CTL["S"]("M"))
        ctl(t_close + 1, CTL["E"](0, "D"))
        ctl(ph.end_ns, CTL["S"]("E"))
        ctl(ph.end_ns, CTL["S"]("C"))
        for f in cfg.faults:
            if f.kind == "halt":
                ctl(f.start_ns, CTL["P"](f.locate, "H", "HALT"))
                if f.call_ns:
                    ctl(f.end_ns, CTL["P"](f.locate, "U", "REOP"))
                    ctl(f.end_ns + f.call_ns, CTL["P"](f.locate, "T", "RESM"))
                else:
                    ctl(f.end_ns, CTL["P"](f.locate, "T", "RESM"))
            elif f.kind in ("drop_session", "refuse_login"):
                s = self.by_name[f.session]
                ctl(f.start_ns, CTL["D"](s.sid))
                ctl(max(f.end_ns, f.start_ns + 1), CTL["L"](s.sid, s.firm_id, "Y" if s.spec.cod else "N"))
        if cfg.halts is not None:
            cfg.halts.schedule(self, v)
        if cfg.feed.snapshot_every_ns:
            t = ph.open_ns
            while t < ph.close_ns:
                push(t, 2, ("snap", v))
                t += cfg.feed.snapshot_every_ns

    # -- the loop ------------------------------------------------------------------------------------------------
    def run(self, until_ns: int | None = None) -> Result:
        bg_recs: list = []
        for bg, s in self.backgrounds:
            v = self.venues[s.venue]
            recs, truth = bg.build(self, v.cfg, [j for j in self._jumps])
            self.truth = truth
            bg_recs += [(t, v.idx, s.sid, m) for t, m in recs]
        bg_recs.sort(key=lambda r: r[0])
        for v in self.venues:
            self._schedule_controls(v)
        for _, ctx in self.agents:
            self._push(min(v.cfg.phases.start_ns for v in self.venues), 3, ("start", ctx))
        script: dict[int, _Sess] = {}
        for t, venue, order in self._scripted:
            vi = self._venue_index(venue)
            if vi not in script:
                script[vi] = self._new_session(SessionSpec(firm="SCRIPT", venue=self.venues[vi].cfg.venue,
                                                           cod=False), f"SCRIPT@{self.venues[vi].cfg.venue}")
                self._push(self.venues[vi].cfg.phases.start_ns, 0,
                           ("ctl", self.venues[vi], CTL["L"](script[vi].sid, script[vi].firm_id, "N")))
            s = script[vi]
            if hasattr(order, "_fields"):             # a raw In_* message
                m = order
            else:
                cl = order.cl_ord_id if order.cl_ord_id is not None else s.next_cl
                s.next_cl = max(s.next_cl, cl + 1)
                m = IN["O"](cl, order.locate, order.side, order.qty, order.price, order.tif, order.display,
                            "Y" if order.post_only else "N", order.display_qty, order.min_qty, order.stp_group,
                            order.stp_mode, order.stop_price)
            self._push(t, 1, ("arrive", self.venues[vi], s.sid, m))
        for t, venue, m in self._controls:
            self._push(t, 0, ("ctl", self.venues[self._venue_index(venue)], m))
        end = until_ns if until_ns is not None else max(v.cfg.phases.end_ns for v in self.venues)
        bi, nb = 0, len(bg_recs)
        heap = self._heap
        while True:
            h = heap[0] if heap else None
            if bi < nb and (h is None or (bg_recs[bi][0], 1) <= (h[0], h[1])):
                t, vi, sid, m = bg_recs[bi]
                bi += 1
                if t > end:
                    break
                self._arrive(t, self.venues[vi], sid, m)
                continue
            if h is None:
                break
            t, cls, _, payload = heapq.heappop(heap)
            if t > end:
                break
            kind = payload[0]
            if kind == "arrive":
                self._arrive(t, payload[1], payload[2], payload[3])
            elif kind == "ctl":
                self._process(t, payload[1], 0, payload[2])
            elif kind == "feed":
                self._deliver_feed(t, *payload[1:])
            elif kind == "rep":
                self._deliver_rep(t, *payload[1:])
            elif kind == "timer":
                self._callback(t, payload[1], "on_timer", payload[2])
            elif kind == "nbbo":
                self._deliver_nbbo(t, *payload[1:])
            elif kind == "start":
                self._callback(t, payload[1], "on_start")
            elif kind == "call":
                payload[1](t, *payload[2:])
            elif kind == "sip_in":
                self._sip_in(t, *payload[1:])
            elif kind == "sip_out":
                self._sip_out(t, *payload[1:])
            elif kind == "snap":
                v = payload[1]
                for i in v.cfg.instruments:
                    v.snaps.append((t, i.locate, v.feed_seq, v.engine.snapshot(i.locate, v.feed_seq, t)))
        return Result(self)

    def _arrive(self, t: int, v: _Venue, sid: int, m) -> None:
        for a, b in v.pause:
            if a <= t < b:
                self._push(b, 1, ("arrive", v, sid, m))
                return
        self._process(t, v, sid, m)

    def _process(self, t: int, v: _Venue, sid: int, m) -> None:
        v.journal.append((t, sid, m))
        feed, reps = v.engine.process(t, sid, m)
        ts = v.engine.ts
        if feed:
            first = v.feed_seq + 1
            v.feed_seq += len(feed)
            v.feed_log.append((ts, first, feed))
            if self._dark_of.get(v.cfg.venue):
                for loc in {m.locate for m in feed if type(m).__name__[-1] in "AEXDUCQ" and m.locate}:
                    b, _, a, _ = v.engine.book(loc).top()
                    ref = (b or 0, a or 0) if b is not None and a is not None else (0, 0)
                    for w in self._dark_of[v.cfg.venue]:
                        if w._ref.get(loc) != ref:
                            w._ref[loc] = ref
                            self._push(ts + w.cfg.reference_ns, 0, ("ctl", w, CTL["N"](loc, *ref)))
            if self.sip is not None:
                for loc in {m.locate for m in feed if type(m).__name__[-1] in "AEXDUCQ" and m.locate}:
                    top = v.engine.book(loc).top()
                    if self._sip_tops.get((v.idx, loc)) != top:
                        self._sip_tops[(v.idx, loc)] = top
                        d = self.sip.venue_ns.get(v.cfg.venue, self.sip.default_ns)
                        self._push(ts + d, 2, ("sip_in", v.cfg.venue, loc, top))
            for _a, ctx in self.agents:
                for s in ctx.sessions:
                    if s.venue == v.idx:
                        arr = max(ts + self._lat(s, 2), s.last_data)
                        s.last_data = arr
                        self._push(arr, 2, ("feed", ctx, s, feed))
        for sess, r in reps:
            if (v.idx, sess) in self._bg_sessions:
                continue
            v.reports.setdefault(sess, []).append(r)
            s = self.sessions.get((v.idx, sess))
            if s is None:
                continue
            for _a, ctx in self.agents:
                if s in ctx.sessions:
                    arr = max(ts + self._lat(s, 1), s.last_ack)
                    s.last_ack = arr
                    self._push(arr, 2, ("rep", ctx, s, r))

    def _sip_in(self, t: int, venue: str, loc: int, top) -> None:
        from firm_nbbo import NbboBuilder, Quote
        nb = self._sip_nbbo.get(loc)
        if nb is None:
            nb = self._sip_nbbo[loc] = NbboBuilder(self.sip.round_lot)
        b, bq, a, aq = top
        before = nb.nbbo()
        nb.update(Quote(venue, b if b is not None else 1, bq if b is not None else 0,
                        a if a is not None else 1, aq if a is not None else 0))
        after = nb.nbbo()
        if after != before:
            self._push(t + self.sip.process_ns, 2, ("sip_out", loc, after))

    def _sip_out(self, t: int, loc: int, nbbo) -> None:
        self.sip_log.append((t, loc, nbbo))
        for _a, ctx in self.agents:
            self._push(t + self.sip.agent_ns, 2, ("nbbo", ctx, loc, nbbo))

    def _deliver_nbbo(self, t: int, ctx: Ctx, loc: int, nbbo) -> None:
        ctx._nbbo[loc] = nbbo
        if type(ctx.agent).on_nbbo is not Agent.on_nbbo:
            self._callback(t, ctx, "on_nbbo", loc, nbbo)

    def _run_cb(self, t: int, ctx: Ctx, fn, *args) -> None:
        t_eff = max(t, ctx._busy)
        ctx.now_ns, ctx._compute, ctx._out = t_eff, 0, []
        fn(*args)
        depart = t_eff + ctx._compute
        ctx._busy = depart
        for s, m in ctx._out:
            v = self.venues[s.venue]
            arr = max(depart + self._lat(s, 0), s.last_entry)
            s.last_entry = arr
            bump = v.bump
            if bump and v.cfg.asymmetric_delay:
                name = type(m).__name__[-1]
                if name in "XM" or (name == "O" and m.post_only == "Y"):
                    bump = 0
            self._push(arr + bump, 1, ("arrive", v, s.sid, m))
        ctx._out = []

    def _callback(self, t: int, ctx: Ctx, name: str, *args) -> None:
        fn = getattr(ctx.agent, name)
        self._run_cb(t, ctx, fn, ctx, *args)

    def _deliver_feed(self, t: int, ctx: Ctx, s: _Sess, feed) -> None:
        tops = {}
        agent = ctx.agent
        wants_feed = type(agent).on_feed is not Agent.on_feed
        for m in feed:
            k = type(m).__name__[-1]
            if k in "AEXDUC" and m.locate:
                bk = ctx.books.get((s.venue, m.locate))
                if bk is None:
                    bk = ctx.books[(s.venue, m.locate)] = MessageBook()
                if k == "A":
                    bk.apply("A", m.ref, 1 if m.side == "B" else -1, m.price, m.shares)
                elif k in "EXC":
                    bk.apply("X", m.ref, qty=m.shares)
                elif k == "D":
                    bk.apply("D", m.ref)
                else:
                    bk.apply("U", m.ref, price=m.price, qty=m.shares, new_ref=m.new_ref)
                tops[m.locate] = None
        if wants_feed:
            def run():
                for m in feed:
                    agent.on_feed(ctx, m)
            self._run_cb(t, ctx, run)
        for loc in tops:
            top = ctx.books[(s.venue, loc)].top()
            if ctx._tops.get((s.venue, loc)) != top:
                ctx._tops[(s.venue, loc)] = top
                self._run_cb(t, ctx, agent.on_book, ctx, loc, top)

    def _deliver_rep(self, t: int, ctx: Ctx, s: _Sess, rep) -> None:
        ctx._on_report(s, rep)
        self._run_cb(t, ctx, ctx.agent.on_report, ctx, rep)


# ---------------------------------------------------------------------------------------------------------------
# results

TAPE_MSG = np.dtype([("t", "f8"), ("kind", "S1"), ("oid", "i8"), ("side", "i1"), ("price", "i8"), ("qty", "i8"),
                     ("agg", "i1"), ("trade", "i8")])
TAPE_TRD = np.dtype([("t", "f8"), ("price", "i8"), ("qty", "i8"), ("sign", "i1"), ("informed", "?"),
                     ("trade", "i8")])
TAPE_TOP = np.dtype([("t", "f8"), ("bid", "i8"), ("bid_qty", "i8"), ("ask", "i8"), ("ask_qty", "i8")])
REPORT = np.dtype([("ts", "i8"), ("session", "U32"), ("type", "U1"), ("cl_ord_id", "i8"), ("qty", "i8"),
                   ("price", "i8"), ("match", "i8"), ("liquidity", "U1"), ("fee", "i8"), ("leaves", "i8"),
                   ("reason", "U1")])


class Result:
    def __init__(self, sim: Simulator):
        self.sim = sim
        self.truth = self._truth()
        self.agents = {name_of(ctx): ctx for _, ctx in sim.agents}

    def _v(self, venue) -> _Venue:
        return self.sim.venues[self.sim._venue_index(venue) if isinstance(venue, str) else venue]

    def engine(self, venue="") -> Engine:
        return self._v(venue).engine

    @property
    def journal(self) -> list:
        return [(t, s, m) for v in self.sim.venues for t, s, m in v.journal]

    def journal_bytes(self, venue="") -> bytes:
        return b"".join(journal_record(t, s, encode("ctl" if s == 0 else "in", m))
                        for t, s, m in self._v(venue).journal)

    def feed_messages(self, venue="") -> list:
        """(ts, seq, message) for every feed message, in order."""
        return [(ts, first + i, m) for ts, first, msgs in self._v(venue).feed_log for i, m in enumerate(msgs)]

    def packets(self, venue="") -> list[tuple[int, bytes]]:
        """The venue's ideal packet stream: (send_ns, MoldUDP64 packet), heartbeats included, end of session last."""
        v = self._v(venue)
        sess, cap, hb = v.cfg.mold_session, v.cfg.feed.max_packet - 20, v.cfg.feed.heartbeat_ns
        out, last_t = [], None
        for ts, first, msgs in v.feed_log:
            if last_t is not None and hb:
                t = last_t + hb
                while t < ts:
                    out.append((t, mold_packet(sess, first, [])))
                    t += hb
            enc = [encode("feed", m) for m in msgs]
            chunk, size, seq = [], 0, first
            for e in enc:
                if chunk and size + 2 + len(e) > cap:
                    out.append((ts, mold_packet(sess, seq, chunk)))
                    seq += len(chunk)
                    chunk, size = [], 0
                chunk.append(e)
                size += 2 + len(e)
            if chunk:
                out.append((ts, mold_packet(sess, seq, chunk)))
            last_t = ts
        if v.feed_log:
            out.append((v.feed_log[-1][0], mold_end(sess, v.feed_seq + 1)))
        return out

    def feed_bytes(self, venue="", line: str = "A") -> bytes:
        """The line's packets, concatenated with a u16 length prefix each (as received, impairments applied)."""
        return b"".join(len(p).to_bytes(2, "big") + p for _, p in self.recorded_packets(venue, line))

    def recorded_packets(self, venue="", line: str = "A") -> list[tuple[int, bytes]]:
        v = self._v(venue)
        fc = v.cfg.feed
        li = fc.lines.index(line)
        key = stream_key(v.cfg.seed, v.idx, 0xFEED, li)
        good, out = True, []
        for n, (t, p) in enumerate(self.packets(venue)):
            arr = t + (fc.line_ns[li] if li < len(fc.line_ns) else 0)
            if any(ln == line and a <= t < b for ln, a, b in fc.outages):
                continue
            if fc.burst_loss:
                p_gb, p_bg, loss_bad = fc.burst_loss
                u = rng_uniform(key, 4 * n)
                good = (u >= p_gb) if good else (u < p_bg)
                if not good and rng_uniform(key, 4 * n + 1) < loss_bad:
                    continue
            if fc.loss and rng_uniform(key, 4 * n + 2) < fc.loss:
                continue
            if fc.jitter_ns:
                arr += int(-fc.jitter_ns * math.log(max(rng_uniform(key, 4 * n + 3), 1e-300)))
            out.append((arr, p))
            if fc.dup and rng_uniform(key ^ 0xD0, n) < fc.dup:
                out.append((arr + 1, p))
        if fc.reorder_window:
            out.sort(key=lambda x: x[0])
        else:
            last = 0
            for i, (a, p) in enumerate(out):
                last = max(last, a)
                out[i] = (last, p)
        return out

    def recorded(self, venue="", line: str = "A") -> bytes:
        """The recorded-file format: (u64 send_ns, u32 length, packet) per packet received on the line."""
        return b"".join(file_record(t, p) for t, p in self.recorded_packets(venue, line))

    def retransmit(self, venue, seq: int, count: int) -> list[bytes]:
        """The retransmission service: packets carrying messages seq .. seq+count-1 from the window."""
        v = self._v(venue)
        fc = v.cfg.feed
        if seq < max(1, v.feed_seq - fc.window + 1) or count <= 0:
            return []
        count = min(count, fc.max_retransmit, v.feed_seq - seq + 1)
        msgs = [encode("feed", m) for _, s, m in self.feed_messages(venue) if seq <= s < seq + count]
        out, chunk, size, s0 = [], [], 0, seq
        for e in msgs:
            if chunk and size + 2 + len(e) > fc.max_packet - 20:
                out.append(mold_packet(v.cfg.mold_session, s0, chunk))
                s0 += len(chunk)
                chunk, size = [], 0
            chunk.append(e)
            size += 2 + len(e)
        if chunk:
            out.append(mold_packet(v.cfg.mold_session, s0, chunk))
        return out

    def snapshot_bytes(self, venue="") -> bytes:
        """The snapshot channel as a recorded file: its own MoldUDP64 session (venue name + 'S'), own sequence."""
        v = self._v(venue)
        sess = (v.cfg.venue[:9] + "S").ljust(10)
        out, seq = [], 1
        for t, _, _, msgs in v.snaps:
            enc = [encode("feed", m) for m in msgs]
            chunk, size = [], 0
            for e in enc:
                if chunk and size + 2 + len(e) > v.cfg.feed.max_packet - 20:
                    out.append(file_record(t, mold_packet(sess, seq, chunk)))
                    seq += len(chunk)
                    chunk, size = [], 0
                chunk.append(e)
                size += 2 + len(e)
            if chunk:
                out.append(file_record(t, mold_packet(sess, seq, chunk)))
                seq += len(chunk)
        return b"".join(out)

    def reports(self, firm: str) -> np.ndarray:
        rows = []
        for (vi, sid), s in self.sim.sessions.items():
            if s.firm != firm:
                continue
            for r in self.sim.venues[vi].reports.get(sid, []):
                t = type(r).__name__[-1]
                g = r._asdict()
                rows.append((r.ts, s.name, t, g.get("new_cl_ord_id", g.get("cl_ord_id", 0)), g.get("qty", 0),
                             g.get("price", 0), g.get("match", 0), g.get("liquidity", ""), g.get("fee", 0),
                             g.get("leaves", 0), g.get("reason", "")))
        rows.sort(key=lambda x: x[0])
        return np.array(rows, dtype=REPORT)

    def drop_copy(self, firm: str) -> np.ndarray:
        r = self.reports(firm)
        return r[np.isin(r["type"], ["E", "C"])]

    def _truth(self) -> dict:
        sim = self.sim
        names = {(vi, sid): s.name for (vi, sid), s in sim.sessions.items()}
        inf = sim.truth.get("informed", {})
        rows = []
        for v in sim.venues:
            for match, loc, px, q, _rs, ags, side, liq, agg_cl in v.engine.trades:
                bg = (v.idx, ags) in sim._bg_sessions
                if liq == "C":
                    cls = "cross"
                elif bg:
                    cls = "informed" if inf.get(agg_cl, False) else "noise"
                else:
                    cls = names.get((v.idx, ags), "?").split("@")[0]
                rows.append((v.idx, match, loc, px, q, side, cls, bool(bg and inf.get(agg_cl, False))))
        tr = np.array(rows, dtype=[("venue", "i4"), ("match", "i8"), ("locate", "i4"), ("price", "i8"),
                                   ("qty", "i8"), ("side", "i1"), ("aggressor", "U32"), ("informed", "?")])
        return {"v_t": sim.truth.get("v_t"), "v": sim.truth.get("v"), "trades": tr, "informed_cl": inf}

    def sip(self, locate: int = 1) -> np.ndarray:
        """The consolidated feed as published: (t_ns, bid, bid_size, ask, ask_size), -1 for a side with no protected
        quotation (Simulator(sip=SipConfig(...)) only)."""
        rows = [(t, n.bid, n.bid_size, n.ask, n.ask_size) if n is not None else (t, -1, 0, -1, 0)
                for t, loc, n in self.sim.sip_log if loc == locate]
        return np.array(rows, dtype=[("t", "i8"), ("bid", "i8"), ("bid_size", "i8"), ("ask", "i8"),
                                     ("ask_size", "i8")])

    def tape(self, venue="", locate: int = 1):
        """The venue's feed for one instrument as a firm_tape.Tape (times in seconds from the open, prices in
        ticks), so that Book 7's replay, feature and mark-out tools run unchanged."""
        from firm_tape import Tape, TapeConfig
        v = self._v(venue)
        inst = next(i for i in v.cfg.instruments if i.locate == locate)
        k, t0 = inst.tick, v.cfg.phases.open_ns
        book = MessageBook()
        msgs, top, trades = [], [], []
        sides: dict[int, int] = {}
        tr = self.truth["trades"]
        informed = {int(r["match"]): bool(r["informed"]) for r in tr[tr["venue"] == v.idx]}
        for ts, _, feed in v.feed_log:
            tt = (ts - t0) / SEC
            for m in feed:
                if m.locate != locate:
                    continue
                kind = type(m).__name__[-1]
                if kind == "A":
                    side = 1 if m.side == "B" else -1
                    sides[m.ref] = side
                    book.apply("A", m.ref, side, m.price, m.shares)
                    msgs.append((tt, b"A", m.ref, side, m.price // k, m.shares, 0, -1))
                elif kind in "EC":
                    side = sides[m.ref]
                    px = (m.price if kind == "C" else book.book.get(m.ref).price) // k
                    book.apply("X", m.ref, qty=m.shares)
                    msgs.append((tt, b"E", m.ref, side, px, m.shares, -side, m.match))
                    trades.append((tt, px, m.shares, -side, informed.get(m.match, False), m.match))
                elif kind == "X":
                    o = book.book.get(m.ref)
                    msgs.append((tt, b"X", m.ref, sides[m.ref], o.price // k, m.shares, 0, -1))
                    book.apply("X", m.ref, qty=m.shares)
                elif kind == "D":
                    o = book.book.get(m.ref)
                    msgs.append((tt, b"X", m.ref, sides[m.ref], o.price // k, o.qty, 0, -1))
                    book.apply("D", m.ref)
                elif kind == "U":
                    o = book.book.get(m.ref)
                    side = sides[m.ref]
                    msgs.append((tt, b"X", m.ref, side, o.price // k, o.qty, 0, -1))
                    book.apply("U", m.ref, price=m.price, qty=m.shares, new_ref=m.new_ref)
                    sides[m.new_ref] = side
                    msgs.append((tt, b"A", m.new_ref, side, m.price // k, m.shares, 0, -1))
                elif kind == "P":
                    trades.append((tt, m.price // k, m.shares, 1 if m.side == "S" else -1, False, m.match))
                    continue
                else:
                    continue
                b, bq, a, aq = book.top()
                top.append((tt, (b or 0) // k, bq, (a or 0) // k, aq))
        cfg = self.sim.truth.get("tape_cfg") or TapeConfig()
        vt = self.sim.truth.get("v_t")
        vv = self.sim.truth.get("v")
        v_t = (np.asarray(vt) - t0) / SEC if vt is not None and len(vt) else np.zeros(1)
        v_ = np.asarray(vv) / k if vv is not None and len(vv) else np.array([inst.start_price / k])
        return Tape(cfg, np.array(msgs, dtype=TAPE_MSG), np.array(trades, dtype=TAPE_TRD),
                    np.array(top, dtype=TAPE_TOP), v_t, v_, 0)


def name_of(ctx: Ctx) -> str:
    return ctx.sessions[0].name.split("@")[0]


# ---------------------------------------------------------------------------------------------------------------
# adapters


class TapeAgentAdapter(Agent):
    """Runs a Book 7 firm_tape agent (on_market(t, top) and on_fill(...) returning action tuples in ticks) on the
    simulator. Latencies come from the SessionSpec; the agent's own delay_data/delay_entry are not used."""

    def __init__(self, agent, locate: int = 1, tick: int = 100, t0_ns: int = OPEN_NS):
        self.inner, self.locate, self.tick, self.t0 = agent, locate, tick, t0_ns
        self.name = getattr(agent, "name", "tapeagent")
        self.cid_cl: dict[int, int] = {}
        self.cl_cid: dict[int, int] = {}

    def _act(self, ctx, actions) -> None:
        for a in actions or ():
            if a[0] == "limit":
                _, cid, side, px, qty = a
                cl = ctx.send(Order(self.locate, "B" if side == 1 else "S", int(qty), int(px) * self.tick))
            elif a[0] == "market":
                _, cid, side, qty = a
                cl = ctx.send(Order(self.locate, "B" if side == 1 else "S", int(qty), 0, tif="I"))
            else:
                cl = self.cid_cl.get(a[1])
                if cl is not None:
                    ctx.cancel(cl)
                continue
            self.cid_cl[cid], self.cl_cid[cl] = cl, cid

    def on_book(self, ctx, locate, top) -> None:
        if locate != self.locate or top[0] is None or top[2] is None:
            return
        t = (ctx.now_ns - self.t0) / SEC
        self._act(ctx, self.inner.on_market(t, (t, top[0] // self.tick, top[1], top[2] // self.tick, top[3])))

    def on_report(self, ctx, rep) -> None:
        if type(rep).__name__ != "Out_E" or rep.cl_ord_id not in self.cl_cid:
            return
        o = next((x for x in ctx.orders.values() if x["cl"] == rep.cl_ord_id), None)
        side = 1 if o is None or o["side"] == "B" else -1
        t = (ctx.now_ns - self.t0) / SEC
        self._act(ctx, self.inner.on_fill(t, self.cl_cid[rep.cl_ord_id], side, rep.price // self.tick, rep.qty,
                                          rep.liquidity == "A"))


class _ReplayCtx:
    def __init__(self, adapter, ctx):
        self.a, self.ctx = adapter, ctx

    def send(self, side: int, price: int, qty: int) -> int:
        vid = len(self.a.vids)
        cl = self.ctx.send(Order(self.a.locate, "B" if side == 1 else "S", int(qty), int(price) * self.a.tick))
        self.a.vids.append(cl)
        self.a.cl_vid[cl] = vid
        return vid

    def cancel(self, vid: int) -> None:
        self.ctx.cancel(self.a.vids[vid])

    def working(self):
        live = {o["cl"] for o in self.ctx.working()}
        return [v for v, cl in enumerate(self.a.vids) if cl in live]

    @property
    def position(self) -> int:
        return self.ctx.position(self.a.locate)


class ReplayStrategyAdapter(Agent):
    """Runs a Book 7 firm_lobreplay Strategy (on_market(ctx, t, snapshot), on_fill(ctx, vid, t, qty, price), prices
    in ticks) on the simulator, so that one strategy can be compared on replay and on a reactive market."""

    def __init__(self, strategy, locate: int = 1, tick: int = 100, t0_ns: int = OPEN_NS):
        self.s, self.locate, self.tick, self.t0 = strategy, locate, tick, t0_ns
        self.name = getattr(strategy, "name", "replaystrategy")
        self.vids: list[int] = []
        self.cl_vid: dict[int, int] = {}

    def on_book(self, ctx, locate, top) -> None:
        if locate != self.locate:
            return
        snap = {"bid": None if top[0] is None else top[0] // self.tick, "bid_qty": top[1],
                "ask": None if top[2] is None else top[2] // self.tick, "ask_qty": top[3]}
        self.s.on_market(_ReplayCtx(self, ctx), (ctx.now_ns - self.t0) / SEC, snap)

    def on_report(self, ctx, rep) -> None:
        if type(rep).__name__ == "Out_E" and rep.cl_ord_id in self.cl_vid:
            self.s.on_fill(_ReplayCtx(self, ctx), self.cl_vid[rep.cl_ord_id], (ctx.now_ns - self.t0) / SEC, rep.qty,
                           rep.price // self.tick)


# ---------------------------------------------------------------------------------------------------------------
# presets


def us_equity_lit(**kw) -> ExchangeConfig:
    """A US-equity lit venue: price-time priority, maker-taker fees per share, one-cent tick."""
    return replace(ExchangeConfig(venue="SIMX"), **kw)


def pro_rata_futures(**kw) -> ExchangeConfig:
    """A futures venue with a top-order allocation then pro rata (Book 1 ch. 19), per-contract fees."""
    inst = InstrumentSpec("FUT1", 1, tick=2500, lot=1, start_price=50_000_000, matching="configurable",
                          alloc={"top_pct": 40, "fifo_pct": 0, "min_alloc": 1})
    return replace(ExchangeConfig(venue="SIMF", instruments=(inst,), fees=FeeSchedule(0.0, 0.0)), **kw)


def midpoint_dark_pool(reference: str = "SIMX", reference_ns: int = 50_000, **kw) -> ExchangeConfig:
    """A dark venue: agents send midpoint pegs (display 'M', optional min_qty); nothing is displayed; the pegs price
    off the lit venue `reference`'s best bid and offer, received reference_ns after each change (control N)."""
    return replace(ExchangeConfig(venue="SIMD", fees=FeeSchedule(0.0010, 0.0010), reference=reference,
                                  reference_ns=reference_ns), **kw)


def speed_bumped(bump_ns: int = 350_000, asymmetric: bool = False, **kw) -> ExchangeConfig:
    return replace(ExchangeConfig(venue="SIMB", speed_bump_ns=bump_ns, asymmetric_delay=asymmetric), **kw)


def periodic_batch(interval_ns: int = 100_000_000, **kw) -> ExchangeConfig:
    return replace(ExchangeConfig(venue="SIMP", batch_interval_ns=interval_ns), **kw)


def auction_venue(**kw) -> ExchangeConfig:
    """Opening and closing auctions with indicative prices every second in the calls and an at-close cut-off."""
    ph = Phases(open_auction=True, close_auction=True, indicative_every_ns=SEC, moc_cutoff_ns=CLOSE_NS - 600 * SEC)
    return replace(ExchangeConfig(venue="SIMA", phases=ph), **kw)


def crypto_venue(**kw) -> ExchangeConfig:
    """A round-the-clock venue: 24-hour session, fees in basis points, a request-weight rate limit."""
    ph = Phases(start_ns=0, open_ns=1, close_ns=86_400 * SEC - 2, end_ns=86_400 * SEC - 1)
    inst = InstrumentSpec("BTCUSD", 1, tick=10_000, lot=1, start_price=600_000_000)
    return replace(ExchangeConfig(venue="SIMC", instruments=(inst,), phases=ph, fees=FeeSchedule(-0.5, 2.5, unit="bp"),
                                  throttle=Throttle(rate=100, burst=200, weights=(("O", 1), ("X", 1), ("U", 1),
                                                                                 ("M", 10), ("Q", 2)))), **kw)


__all__ = ["InstrumentSpec", "FeeSchedule", "Phases", "Throttle", "FeedConfig", "Fault", "ExchangeConfig",
           "LatencyModel", "SessionSpec", "Order", "Agent", "Simulator", "Result", "TapeBackground",
           "TapeAgentAdapter", "ReplayStrategyAdapter", "field"]


def main(argv=None) -> None:
    """python -m firm_exchsim serve --config cfg.json [--seconds N]"""
    import argparse
    ap = argparse.ArgumentParser(prog="firm_exchsim")
    ap.add_argument("command", choices=["serve"])
    ap.add_argument("--config", required=True)
    ap.add_argument("--seconds", type=float, default=0.0)
    a = ap.parse_args(argv)
    from firm_exchsim_serve import serve
    serve(a.config, a.seconds)


if __name__ == "__main__":
    main()
