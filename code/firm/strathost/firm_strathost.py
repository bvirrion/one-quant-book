"""firm.strathost -- one strategy object in several environments, and the parity harness (One Quant Book 15, ch. 12).

A strategy is written against three abstractions and nothing else: a clock (`ctx.now`, `ctx.set_timer`), market data
(`on_book(ctx, top)` with integer prices in 1/10,000) and order entry (`ctx.send`, `ctx.cancel`, `ctx.working()`,
`ctx.position`, and the callbacks `on_ack`, `on_fill`, `on_cancel`, `on_reject`). The host delivers its inputs in the
event model of firm.btengine (chapter 11): inputs with the same time are delivered in a fixed class order (market,
then order entry, then timers), whatever order the environment produced them in.

Environments (all on Book 10's firm.exchsim with a firm.tape session as background flow):
    'sim'      the simulator in process: the environment adapter calls the simulator's agent context directly
    'prod'     production-shaped: orders go through Book 13's gateway (firm.ordergw.Gateway: state machine,
               throttle, exposure) and are encoded as OUCH-style messages in SoupBinTCP frames on an in-memory byte
               stream; reports come back as encoded bytes; every input is journalled in Book 13's input-journal format
               (firm.binlog.journal_write: receive time + 48-byte record)
    'replay'   the journal of a run, replayed into a fresh strategy: the backtest of recorded inputs
Four planted defects (Defects(...)), each off by default:
    wall_clock      the strategy reads the machine's clock (machine_ns()) instead of ctx.now
    float_prices    the prod adapters hand the strategy prices as float currency and convert back with int()
    arrival_order   the host delivers simultaneous inputs in arrival order (prod reads order entry first)
    acked_working   prod's working() lists only acknowledged orders (sim's lists pending ones too)

API (stable):
    HostedStrategy       on_start, on_book, on_ack, on_fill, on_cancel, on_reject, on_timer (override what you need)
    Defects(wall_clock=False, float_prices=False, arrival_order=False, acked_working=False)
    run_env(env, strategy, seconds, seed, defects, latency_ns=20_000) -> HostRun   env 'sim' or 'prod'
    replay(journal_bytes, strategy, defects) -> HostRun
    HostRun: outputs [(t, 'order', oid, side, price, qty) | (t, 'cancel', oid)], inputs [(t, cls, ...)],
             journal (bytes, prod only), position
    compare(a, b) -> Parity(first, events_before, affected, same)     first differing output and its context
    machine_ns(); set_machine_clock(fn)   the machine's clock as the strategy would read it (time.time_ns by default)
"""
from __future__ import annotations

import pathlib
import sys
import time
from dataclasses import dataclass, field

FIRM = pathlib.Path(__file__).resolve().parents[1]
for _c in ("exchsim", "tape", "ordergw", "binlog", "feedhandler", "feed"):
    sys.path.insert(0, str(FIRM / _c))
import firm_exchsim as X  # noqa: E402
import firm_exchsim_codec as C  # noqa: E402
from firm_binlog import journal_read, journal_write  # noqa: E402
from firm_feedhandler import EVENT  # noqa: E402
from firm_ordergw import Gateway  # noqa: E402
from firm_tape import TapeConfig  # noqa: E402

RANK = {"book": 0, "ack": 1, "fill": 1, "cancel": 1, "reject": 1, "timer": 2}
KIND = {"book": b"B", "ack": b"A", "fill": b"E", "cancel": b"C", "reject": b"J", "timer": b"T"}
CLS = {v: k for k, v in KIND.items()}
SCALE = 10_000

_machine = time.time_ns


def machine_ns() -> int:
    """The machine's clock, as a strategy that reads it directly would see it."""
    return _machine()


def set_machine_clock(fn) -> None:
    global _machine
    _machine = fn


@dataclass(frozen=True)
class Defects:
    wall_clock: bool = False
    float_prices: bool = False
    arrival_order: bool = False
    acked_working: bool = False


FIXED = Defects()


class HostedStrategy:
    def on_start(self, ctx) -> None: ...
    def on_book(self, ctx, top) -> None: ...
    def on_ack(self, ctx, oid) -> None: ...
    def on_fill(self, ctx, oid, qty, price) -> None: ...
    def on_cancel(self, ctx, oid) -> None: ...
    def on_reject(self, ctx, oid) -> None: ...
    def on_timer(self, ctx, tag) -> None: ...


@dataclass
class HostRun:
    outputs: list = field(default_factory=list)
    marks: list = field(default_factory=list)        # inputs delivered before each output
    inputs: list = field(default_factory=list)
    journal: bytes = b""
    position: int = 0
    start: int = 0


# ------------------------------------------------------------ the host
class Host:
    """Holds the strategy, its context and the event model; an environment adapter feeds it inputs."""

    def __init__(self, strategy: HostedStrategy, env, defects: Defects):
        self.s, self.env, self.d = strategy, env, defects
        self.run, self.now, self.buf = HostRun(), 0, []
        self.orders: dict[int, dict] = {}          # oid -> side, price, qty, filled, state
        self.position, self.next_oid = 0, 0

    # -- the context the strategy sees
    def send(self, side: int, price, qty: int) -> int:
        oid, self.next_oid = self.next_oid, self.next_oid + 1
        self.orders[oid] = {"side": side, "price": price, "qty": qty, "filled": 0, "state": "pending"}
        mark = len(self.run.inputs)
        wire = self.env.send(oid, side, price, qty)            # the price that leaves, in 1/10,000
        self.run.outputs.append((self.now, "order", oid, side, wire, qty))
        self.run.marks.append(mark)
        return oid

    def cancel(self, oid: int) -> None:
        if self.orders[oid]["state"] in ("pending", "live"):
            self.orders[oid]["state"] = "cancelling"
            self.run.outputs.append((self.now, "cancel", oid))
            self.run.marks.append(len(self.run.inputs))
            self.env.cancel(oid)

    def working(self) -> list[int]:
        states = ("live",) if self.env.acked_only else ("pending", "live")
        return [o for o, v in self.orders.items() if v["state"] in states]

    def set_timer(self, delay_ns: int, tag: int) -> None:
        self.env.set_timer(delay_ns, tag)

    # -- inputs, buffered per time and delivered in the event model's order
    def input(self, t: int, cls: str, *args) -> None:
        self.buf.append((t, cls, args))

    def flush(self) -> None:
        batch, self.buf = self.buf, []
        if not self.d.arrival_order:          # the event model; stable within a class
            batch.sort(key=lambda x: (x[0], RANK[x[1]]))
        else:                                 # as the adapter read them: order entry first
            batch.sort(key=lambda x: (x[0], x[1] == "book"))
        for t, cls, args in batch:
            self.now = t
            self.run.inputs.append((t, cls) + tuple(args))
            self._dispatch(cls, args)

    def _dispatch(self, cls: str, a) -> None:
        o = self.orders.get(a[0]) if cls not in ("book", "timer") else None
        if cls not in ("book", "timer") and o is None:
            return                              # a replayed report for an order this run never sent
        if cls == "book":
            self.s.on_book(self, a)
        elif cls == "ack":
            if o["state"] == "pending":
                o["state"] = "live"
            self.s.on_ack(self, a[0])
        elif cls == "fill":
            o["filled"] += a[1]
            self.position += o["side"] * a[1]
            if o["filled"] >= o["qty"]:
                o["state"] = "done"
            self.s.on_fill(self, a[0], a[1], a[2])
        elif cls in ("cancel", "reject"):
            o["state"] = "done"
            (self.s.on_cancel if cls == "cancel" else self.s.on_reject)(self, a[0])
        else:
            self.s.on_timer(self, a[0])


# ------------------------------------------------------------ environments on the simulator
class _SimAgent(X.Agent):
    """The environment adapter for 'sim' and 'prod': an agent of the simulator that feeds the host."""

    name = "hosted"

    def __init__(self, env):
        self.env = env

    def _flush_soon(self, ctx) -> None:
        if not self.env.flush_pending:
            self.env.flush_pending = True
            ctx.set_timer(0, "flush")                  # runs after every input of this instant

    def on_start(self, ctx) -> None:
        self.env.ctx = ctx
        self.env.host.now = self.env.host.run.start = ctx.now_ns
        self.env.host.s.on_start(self.env.host)

    def on_book(self, ctx, locate, top) -> None:
        self.env.ctx = ctx
        if top[0] is not None and top[2] is not None:
            self.env.host.input(ctx.now_ns, "book", *self.env.price_in(top))
            self._flush_soon(ctx)

    def on_report(self, ctx, rep) -> None:
        self.env.ctx = ctx
        self.env.report(ctx.now_ns, rep)
        self._flush_soon(ctx)

    def on_timer(self, ctx, tag) -> None:
        self.env.ctx = ctx
        if tag == "flush":
            self.env.flush_pending = False
            self.env.host.now = ctx.now_ns
            self.env.host.flush()
        else:
            self.env.host.input(ctx.now_ns, "timer", tag)
            self._flush_soon(ctx)


class SimEnv:
    """The simulator in process: orders and reports are the simulator's objects."""

    acked_only = False

    def __init__(self, strategy, defects: Defects):
        self.host, self.ctx, self.flush_pending = Host(strategy, self, defects), None, False
        self.cl_oid: dict[int, int] = {}
        self.oid_cl: dict[int, int] = {}
        self.done: set[int] = set()          # finished by a report already received (not yet delivered)

    def price_in(self, top):
        return top                                        # (bid, bid_qty, ask, ask_qty), integers

    def price_out(self, price) -> int:
        return int(price)

    def send(self, oid, side, price, qty) -> int:
        px = self.price_out(price)
        cl = self.ctx.send(X.Order(1, "B" if side == 1 else "S", int(qty), px))
        self.cl_oid[cl], self.oid_cl[oid] = oid, cl
        return px

    def cancel(self, oid) -> None:
        if oid not in self.done:             # as the gateway does: never cancel a finished order
            self.ctx.cancel(self.oid_cl[oid])

    def set_timer(self, delay_ns, tag) -> None:
        self.ctx.set_timer(delay_ns, tag)

    def report(self, t, rep) -> None:
        k = type(rep).__name__[-1]
        oid = self.cl_oid.get(getattr(rep, "cl_ord_id", None))
        if oid is None:
            return
        if (k == "E" and rep.leaves == 0) or k in "CJ":
            self.done.add(oid)
        if k == "A":
            self.host.input(t, "ack", oid)
        elif k == "E":
            self.host.input(t, "fill", oid, rep.qty, self.price_in((rep.price, 0, rep.price, 0))[0])
        elif k == "C" and rep.decrement:
            self.host.input(t, "cancel", oid)
        elif k == "J":
            self.host.input(t, "reject", oid)


class ProdEnv(SimEnv):
    """Production-shaped: Book 13's gateway, encoded messages on a byte stream, a journal."""

    def __init__(self, strategy, defects: Defects):
        super().__init__(strategy, defects)
        self.gw = Gateway(rate_per_s=10_000, burst=100, max_long=1_000, max_short=1_000)
        self.acked_only = defects.acked_working
        self.float = defects.float_prices
        self.to_venue, self.to_client = bytearray(), bytearray()
        self.records: list = []
        self.n = 0

    def price_in(self, top):
        if not self.float:
            return top
        return tuple(x / SCALE if i % 2 == 0 else x for i, x in enumerate(top))   # float currency

    def price_out(self, price) -> int:
        return int(price * SCALE) if self.float else int(price)      # int() truncates

    def send(self, oid, side, price, qty) -> int:
        px = self.price_out(price)
        side_ = "B" if side == 1 else "S"
        verdict, msg = self.gw.new(self.ctx.now_ns, oid + 1, side_, int(qty), px)
        if verdict != "send":
            self.host.input(self.ctx.now_ns, "reject", oid)
            return px
        o = C.NT["in"]["O"](msg[1], 1, msg[2], msg[3], msg[4], "D", "Y", "N", 0, 0, 0, "N", 0)
        self.to_venue += C.soup_frame("U", C.encode("in", o))
        self._pump_venue()
        return px

    def cancel(self, oid) -> None:
        verdict, msg = self.gw.cancel(self.ctx.now_ns, oid + 1)
        if verdict == "send":
            self.to_venue += C.soup_frame("U", C.encode("in", C.NT["in"]["X"](msg[1], 0)))
            self._pump_venue()

    def _pump_venue(self) -> None:
        """The venue side of the byte stream: whole frames become the simulator's orders."""
        frames, rest = C.soup_parse(bytes(self.to_venue))
        self.to_venue = bytearray(rest)
        for _typ, payload in frames:
            m = C.decode("in", payload)
            if type(m).__name__ == "In_O":
                self.ctx.send(X.Order(1, m.side, m.qty, m.price, cl_ord_id=m.cl_ord_id))
            else:
                self.ctx.cancel(m.cl_ord_id)

    def report(self, t, rep) -> None:
        if not hasattr(rep, "cl_ord_id"):
            return                                        # session and system messages
        self.to_client += C.soup_frame("S", C.encode("out", rep))
        frames, rest = C.soup_parse(bytes(self.to_client))
        self.to_client = bytearray(rest)
        for _typ, payload in frames:
            r = C.decode("out", payload)
            k = type(r).__name__[-1]
            f = {"qty": getattr(r, "qty", 0), "price": getattr(r, "price", 0), "leaves": getattr(r, "leaves", 0)}
            self.gw.on_report(t, k, r.cl_ord_id, **f)
            oid = r.cl_ord_id - 1
            if k == "A":
                self.host.input(t, "ack", oid)
            elif k == "E":
                self.host.input(t, "fill", oid, r.qty, self.price_in((r.price, 0, r.price, 0))[0])
            elif k == "C" and r.decrement:
                self.host.input(t, "cancel", oid)
            elif k == "J":
                self.host.input(t, "reject", oid)


def _journal(inputs) -> bytes:
    """Inputs as delivered, in Book 13's input-journal format: receive time + a 48-byte record."""
    recs = []
    for n, x in enumerate(inputs):
        t, cls = x[0], x[1]
        if cls == "book":
            b, bq, a, aq = (round(v * SCALE) if isinstance(v, float) else v for v in x[2:6])
            ev = EVENT.pack(KIND[cls][0], 0, 1, n, t, b, a, bq, aq)
        elif cls == "fill":
            px = round(x[4] * SCALE) if isinstance(x[4], float) else x[4]
            ev = EVENT.pack(KIND[cls][0], 0, 1, n, t, x[2], 0, px, x[3])
        else:
            ev = EVENT.pack(KIND[cls][0], 0, 1, n, t, x[2], 0, 0, 0)
        recs.append((t, ev))
    return journal_write(recs)


def _venue(seconds: float) -> X.ExchangeConfig:
    o, s = X.OPEN_NS, X.SEC
    ph = X.Phases(start_ns=o - s, open_ns=o, close_ns=o + int(seconds) * s, end_ns=o + int(seconds + 1) * s)
    return X.ExchangeConfig(phases=ph, fees=X.FeeSchedule(make=0.0, take=0.0))


def machine_clock(host: Host, base_ns: int, rate: float):
    """A machine clock for a harness: `base_ns` when the host starts, advancing `1 / rate` times as fast as the
    host's time (rate 1: production, where the machine runs with the venue; rate 100: a replay 100 times faster).
    base_ns None: the host's own start time (the machine's clock is the venue's)."""
    return lambda: (host.run.start if base_ns is None else base_ns) + int((host.now - host.run.start) / rate)


def run_env(env: str, strategy: HostedStrategy, seconds: float = 3600.0, seed: int = 1,
            defects: Defects = FIXED, latency_ns: int = 20_000, machine=None) -> HostRun:
    e = (ProdEnv if env == "prod" else SimEnv)(strategy, defects)
    if machine is not None:
        set_machine_clock(machine_clock(e.host, *machine))
    sim = X.Simulator(_venue(seconds), seed=1)
    sim.add_background(X.TapeBackground(TapeConfig(seconds=seconds, seed=seed, news_at=None)))
    lm = X.LatencyModel(entry_ns=latency_ns, ack_ns=latency_ns, data_ns=latency_ns)
    sim.add_agent(_SimAgent(e), X.SessionSpec("HOST", latency=lm))
    sim.run()
    run = e.host.run
    run.position = e.host.position
    if env == "prod":
        run.journal = _journal(run.inputs)
    return run


# ------------------------------------------------------------ the replay environment
class _ReplayEnv:
    acked_only = False

    def __init__(self):
        self.timers: list = []

    def send(self, oid, side, price, qty) -> int:
        return int(price)

    def cancel(self, oid) -> None:
        pass

    def set_timer(self, delay_ns, tag) -> None:
        pass                                              # timers fired in production are in the journal


def replay(journal: bytes, strategy: HostedStrategy, defects: Defects = FIXED,
           start_ns: int = 0, machine=None) -> HostRun:
    """Feed a production journal's inputs to a fresh strategy, instant by instant."""
    env = _ReplayEnv()
    host = Host(strategy, env, defects)
    host.now = host.run.start = start_ns
    if machine is not None:
        set_machine_clock(machine_clock(host, *machine))
    strategy.on_start(host)
    recs = journal_read(journal)
    i = 0
    while i < len(recs):
        t = recs[i][0]
        while i < len(recs) and recs[i][0] == t:
            k, _s, _l, _n, ts, ref, ref2, price, qty = EVENT.unpack(recs[i][1])
            cls = CLS[bytes([k])]
            if cls == "book":
                host.input(ts, "book", ref, price, ref2, qty)
            elif cls == "fill":
                host.input(ts, "fill", ref, qty, price)
            else:
                host.input(ts, cls, ref)
            i += 1
        host.flush()
    host.run.position = host.position
    return host.run


# ------------------------------------------------------------ the parity harness
@dataclass
class Parity:
    same: bool
    first: int                      # index of the first differing output, -1 if none
    events_before: int              # inputs delivered in run a before that output
    affected: int                   # outputs of run a with no identical output in run b
    t_first: int = -1


def compare(a: HostRun, b: HostRun) -> Parity:
    n = min(len(a.outputs), len(b.outputs))
    first = next((i for i in range(n) if a.outputs[i] != b.outputs[i]), -1)
    if first < 0 and len(a.outputs) != len(b.outputs):
        first = n
    if first < 0:
        return Parity(True, -1, len(a.inputs), 0)
    pool: dict = {}
    for x in b.outputs:
        pool[x] = pool.get(x, 0) + 1
    affected = 0
    for x in a.outputs:
        if pool.get(x, 0):
            pool[x] -= 1
        else:
            affected += 1
    src = a if first < len(a.outputs) else b
    return Parity(False, first, src.marks[first], affected, src.outputs[first][0])

