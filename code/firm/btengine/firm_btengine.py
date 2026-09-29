"""firm.btengine -- one backtest engine over four fidelity levels (build of One Quant Book 15, chapter 11).

The firm's three backtesters of One Quant Book 7 (firm.vecbt, level 1; firm.evbt, level 2; firm.lobreplay, level 3)
and the exchange simulator of One Quant Book 10 (firm.exchsim, used as level 4: a reactive simulation, the
simulator standing in for the venue) run behind one interface. They are wrapped, never edited: each level has an
adapter that turns one strategy object into what the backtester expects and turns what the strategy saw and did
back into one event model. Every run is recorded in a results store with its manifest (level, strategy and engine
code hashes, data snapshot hashes, parameters, seed), so that two runs can be compared event by event.

Strategies:
    TargetStrategy   target(close, i) -> weight held from the next bar (one rule, run vectorised at level 1
                     through targets(close), event by event at level 2)
    QuoteStrategy    on_market(ctx, t, snap) and on_fill(ctx, oid, t, qty, price), prices in ticks; ctx.send(side,
                     price, qty) -> oid, ctx.cancel(oid), ctx.working() -> [oid], ctx.position (levels 2-4)

Event model: every run records Event(t, cls, seq, data) in the total order (t, class rank, seq):
    CLASSES = ('market', 'fill', 'order', 'cancel')   the market first, then what it did to us, then what we did
Data access: DataAccess(root) stores named datasets as Parquet with a content hash (the snapshot identity):
    put(name, table) -> hash, get(name) -> pyarrow.Table, hash(name), tape(seconds, seed), daily(days, seed)
Results store: ResultsStore(root).save(run) -> run_id (the hash of the manifest), load(run_id), query(**eq)

API (stable):
    Engine(level, strategy, data, config).run() -> Run
        config: dataset (name), latency (s), seed, fill ('touch'), queue ('fifo'), bar (s, level 2), cost
    Run: level, pnl, position, fills (t, side, qty, price), events [Event], mids (t, mid), manifest
    first_divergence(run_a, run_b, cls='fill') -> (index, event_a, event_b) or None
    classify_fills(reactive, replay, tol) -> array of bool (True: the fill has no replay counterpart)
    markouts(run, horizon) -> per-fill markout in ticks x shares (mid `horizon` s later minus price, signed)
"""
from __future__ import annotations

import hashlib
import heapq
import inspect
import json
import pathlib
import sys
from dataclasses import dataclass, field

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

FIRM = pathlib.Path(__file__).resolve().parents[1]
for _c in ("vecbt", "evbt", "lobreplay", "exchsim", "tape", "bars", "workflow", "feed"):
    sys.path.insert(0, str(FIRM / _c))
import firm_evbt  # noqa: E402
import firm_exchsim as X  # noqa: E402
import firm_lobreplay  # noqa: E402
from firm_bars import Bars, asof, time_bars  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402
from firm_vecbt import backtest  # noqa: E402
from firm_workflow import content_hash  # noqa: E402

LEVELS = (1, 2, 3, 4)
CLASSES = ("market", "fill", "order", "cancel")
RANK = {c: i for i, c in enumerate(CLASSES)}


# ------------------------------------------------------------ event model
@dataclass(order=True, frozen=True)
class Event:
    t: float                        # seconds from the session start (level 1-2: bar end)
    rank: int                       # RANK[cls]: simultaneous events in a fixed class order
    seq: int                        # arrival order within the run: ties broken the same way
    cls: str = field(compare=False)
    data: tuple = field(compare=False, default=())


class EventLog:
    def __init__(self):
        self.events: list[Event] = []

    def add(self, t: float, cls: str, *data) -> None:
        self.events.append(Event(float(t), RANK[cls], len(self.events), cls, tuple(data)))

    def ordered(self) -> list[Event]:
        return sorted(self.events)


# ------------------------------------------------------------ strategies
class TargetStrategy:
    """A position rule on closes: target(close, i) is decided at bar i's close, held from bar i + 1."""

    def target(self, close: np.ndarray, i: int) -> float:
        raise NotImplementedError

    def targets(self, close: np.ndarray) -> np.ndarray:
        return np.array([self.target(close, i) for i in range(len(close))])


class QuoteStrategy:
    name = "quote"

    def on_market(self, ctx, t: float, snap: dict) -> None:
        pass

    def on_fill(self, ctx, oid: int, t: float, qty: int, price: int) -> None:
        pass


# ------------------------------------------------------------ data access
class DataAccess:
    """Named datasets stored as Parquet; a dataset's content hash identifies the data a run read."""

    def __init__(self, root):
        self.root = pathlib.Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> pathlib.Path:
        return self.root / (name.replace("/", "__") + ".parquet")

    def put(self, name: str, table: pa.Table, meta: dict | None = None) -> str:
        h = content_hash({c: table[c].to_numpy() for c in table.column_names})
        md = {b"hash": h.encode(), b"meta": json.dumps(meta or {}, sort_keys=True).encode()}
        pq.write_table(table.replace_schema_metadata(md), self._path(name))
        return h

    def exists(self, name: str) -> bool:
        return self._path(name).exists()

    def get(self, name: str) -> pa.Table:
        return pq.read_table(self._path(name))

    def hash(self, name: str) -> str:
        return pq.read_schema(self._path(name)).metadata[b"hash"].decode()

    def meta(self, name: str) -> dict:
        return json.loads(pq.read_schema(self._path(name)).metadata[b"meta"])

    def tape(self, seconds: float = 3600.0, seed: int = 7) -> str:
        """A firm.tape session (Book 7) stored as its messages; returns the dataset's name."""
        name = f"tape/s{int(seconds)}/seed{seed}"
        if not self.exists(name):
            tp = simulate(TapeConfig(seconds=seconds, seed=seed, news_at=None))
            cols = {k: tp.msgs[k] for k in tp.msgs.dtype.names}
            cols["kind"] = tp.msgs["kind"].view(np.uint8)          # b'A', b'X', b'E' as bytes
            self.put(name, pa.table(cols),
                     {"seconds": seconds, "seed": seed, "kind": "tape"})
        return name

    def daily(self, days: int = 1000, seed: int = 11) -> str:
        """Synthetic daily bars of one instrument (open, close), with overnight gaps."""
        name = f"daily/d{days}/seed{seed}"
        if not self.exists(name):
            rng = np.random.default_rng(seed)
            gap = 0.004 * rng.standard_normal(days)                         # close to next open
            day = 0.0002 + 0.011 * rng.standard_normal(days) + 0.0015 * np.sin(np.arange(days) / 40)
            close = 100 * np.exp(np.cumsum(gap + day))
            open_ = close * np.exp(-day)
            self.put(name, pa.table({"day": np.arange(days), "open": open_, "close": close}),
                     {"days": days, "seed": seed, "kind": "daily"})
        return name


def msgs_of(table: pa.Table) -> np.ndarray:
    from firm_tape import MSG
    out = np.empty(table.num_rows, dtype=MSG)
    for k in MSG.names:
        col = table[k].to_numpy()
        out[k] = col.astype(np.uint8).view("S1") if k == "kind" else col
    return out


def top_of(msgs: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Top of book after every message, rebuilt with Book 7's replay book (times, bid, ask in ticks)."""
    b = firm_lobreplay.Book()
    t, bid, ask = np.empty(len(msgs)), np.empty(len(msgs)), np.empty(len(msgs))
    for i, m in enumerate(msgs):
        b.apply(m)
        x, y = b.best(1), b.best(-1)
        t[i], bid[i], ask[i] = m["t"], np.nan if x is None else x, np.nan if y is None else y
    return t, bid, ask


# ------------------------------------------------------------ runs
@dataclass
class Run:
    level: int
    pnl: float
    position: float
    fills: np.ndarray                   # (n, 4): t, side, qty, price
    events: list
    mids: np.ndarray                    # (m, 2): t, mid (ticks) as the strategy saw it
    manifest: dict

    @property
    def run_id(self) -> str:
        return content_hash(self.manifest)[:16]


def code_hash(obj) -> str:
    src = inspect.getsource(obj if inspect.isclass(obj) else type(obj))
    return hashlib.sha256(src.encode()).hexdigest()[:16]


ENGINE_CODE = hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()[:16]


class _Ctx:
    """The one context a QuoteStrategy sees at every level: send, cancel, working, position."""

    def __init__(self, backend, log: EventLog):
        self.b, self.log, self.now, self.live = backend, log, 0.0, set()

    def send(self, side: int, price: int, qty: int) -> int:
        oid = self.b.send(side, price, qty)
        self.live.add(oid)
        self.log.add(self.now, "order", oid, side, int(price), int(qty))
        return oid

    def cancel(self, oid: int) -> None:
        self.b.cancel(oid)
        self.live.discard(oid)
        self.log.add(self.now, "cancel", oid)

    def working(self) -> list[int]:
        return sorted(self.live & set(self.b.working()))

    @property
    def position(self) -> int:
        return int(self.b.position())


@dataclass
class _Back:
    """What a level offers the context: send, cancel, working, position (callables)."""
    send: object
    cancel: object
    working: object
    position: object


class _Wrap:
    """Records what the strategy saw (market) and what reached it (fills) before calling it."""

    def __init__(self, strategy: QuoteStrategy, ctx: _Ctx):
        self.s, self.ctx, self.mids, self.side = strategy, ctx, [], {}

    def market(self, t: float, snap: dict) -> None:
        self.ctx.now = t
        if snap["bid"] is not None and snap["ask"] is not None:
            self.mids.append((t, 0.5 * (snap["bid"] + snap["ask"])))
            self.ctx.log.add(t, "market", int(snap["bid"]), int(snap["ask"]))
        self.s.on_market(self.ctx, t, snap)

    def fill(self, oid: int, t: float, qty: int, price: int, side: int) -> None:
        self.ctx.now = t
        self.ctx.log.add(t, "fill", oid, side, int(qty), int(price))
        self.s.on_fill(self.ctx, oid, t, qty, price)


# ------------------------------------------------------------ the engine
class Engine:
    def __init__(self, level: int, strategy, data: DataAccess, config: dict):
        if level not in LEVELS:
            raise ValueError(f"level {level} not in {LEVELS}")
        if level == 1 and not isinstance(strategy, TargetStrategy):
            raise TypeError("level 1 runs a TargetStrategy: no orders, no queues")
        self.level, self.strategy, self.data = level, strategy, data
        self.cfg = dict(config)

    def manifest(self, pnl: float, n_fills: int) -> dict:
        name = self.cfg["dataset"]
        return {"level": self.level, "strategy": type(self.strategy).__name__,
                "strategy_code": code_hash(self.strategy), "engine_code": ENGINE_CODE,
                "data": {name: self.data.hash(name)},
                "params": {k: v for k, v in sorted(self.cfg.items()) if k != "dataset"},
                "seed": self.cfg.get("seed", 0), "pnl": round(float(pnl), 6),
                "fills": n_fills}

    def run(self) -> Run:
        level = {1: self._level1, 2: self._level2, 3: self._level3, 4: self._level4}
        pnl, pos, fills, log, mids = level[self.level]()
        fills = np.array(fills, dtype=float).reshape(-1, 4)
        mids = np.array(mids).reshape(-1, 2)
        return Run(self.level, pnl, pos, fills, log.ordered(), mids,
                   self.manifest(pnl, len(fills)))

    # -- level 1: firm.vecbt
    def _level1(self):
        d = self.data.get(self.cfg["dataset"])
        close = d["close"].to_numpy()
        w = self.strategy.targets(close)
        rets = np.r_[0.0, close[1:] / close[:-1] - 1.0]
        res = backtest(w[:, None], rets[:, None], lag=1, cost=self.cfg.get("cost", 0.0))
        log = EventLog()
        for i in np.flatnonzero(np.abs(res.trades[:, 0]) > 0):
            log.add(float(i), "fill", -1, int(np.sign(res.trades[i, 0])), float(res.trades[i, 0]),
                    float(close[i - 1]) if i else float(close[0]))
        return float(res.capital[-1] - 1.0), float(res.weights[-1, 0]), [], log, []

    # -- level 2: firm.evbt
    def _level2(self):
        if isinstance(self.strategy, TargetStrategy):
            return self._level2_target()
        msgs = msgs_of(self.data.get(self.cfg["dataset"]))
        ex = msgs[msgs["kind"] == b"E"]
        width = self.cfg.get("bar", 1.0)
        b = time_bars(ex["t"], ex["price"], ex["qty"], width, 0.0, float(np.ceil(msgs["t"][-1])))
        keep = b.n > 0                                  # bars with trades: an empty bar is no price
        b = Bars(*(getattr(b, f)[keep] for f in Bars.__dataclass_fields__))
        tt, bid, ask = top_of(msgs)
        at_b, at_a = asof(tt, bid, b.end), asof(tt, ask, b.end)
        log, fills = EventLog(), []
        wrap = None

        class Adapter(firm_evbt.Strategy):
            def on_bar(self, eng, i, bar):
                ok = not (np.isnan(at_b[i]) or np.isnan(at_a[i]))
                snap = {"bid": int(at_b[i]) if ok else None, "ask": int(at_a[i]) if ok else None}
                wrap.market(bar["end"], snap)

            def on_fill(self, eng, f):
                side = 1 if f.qty > 0 else -1
                fills.append((f.t, side, abs(f.qty), f.price))
                wrap.fill(f.oid, f.t, int(abs(f.qty)), int(f.price), side)

        eng = firm_evbt.Engine(b, Adapter(), firm_evbt.TouchFill(),
                               latency=self.cfg.get("latency", 0.0), capital=1.0)
        back = _Back(lambda side, price, qty: eng.submit(side, qty, "limit", price), eng.cancel,
                     lambda: [o.oid for o in eng.working()], lambda: eng.position)
        wrap = _Wrap(self.strategy, _Ctx(back, log))
        with np.errstate(divide="ignore", invalid="ignore"):      # its returns are not used here
            eng.run()
        mid = wrap.mids[-1][1] if wrap.mids else 0.0
        return eng.cash - 1.0 + eng.position * mid, eng.position, fills, log, wrap.mids

    def _level2_target(self):
        d = self.data.get(self.cfg["dataset"])
        close, open_ = d["close"].to_numpy(), d["open"].to_numpy()
        n = len(close)
        b = Bars(np.arange(n) - 0.5, np.arange(n) + 0.5, open_, np.maximum(open_, close),
                 np.minimum(open_, close), close, np.ones(n), close, close, np.ones(n), np.arange(n), np.arange(n))
        strat, log, fills = self.strategy, EventLog(), []

        class Adapter(firm_evbt.Strategy):
            def on_bar(self, eng, i, bar):
                want = strat.target(close, i) * (eng.cash + eng.position * bar["close"])
                delta = want / bar["close"] - eng.position
                if abs(delta) > 1e-12:
                    eng.submit(1 if delta > 0 else -1, abs(delta), "market")
                    log.add(bar["end"], "order", len(eng.orders) - 1, int(np.sign(delta)), 0, abs(delta))

            def on_fill(self, eng, f):
                fills.append((f.t, 1 if f.qty > 0 else -1, abs(f.qty), f.price))
                log.add(f.t, "fill", f.oid, 1 if f.qty > 0 else -1, abs(f.qty), f.price)

        eng = firm_evbt.Engine(b, Adapter(), firm_evbt.TouchFill(), latency=0.0, capital=1.0,
                               policy="optimistic")
        res, _, _ = eng.run()
        return float(res.capital[-1] - 1.0), float(res.weights[-1, 0]), fills, log, []

    # -- level 3: firm.lobreplay
    def _level3(self):
        msgs = msgs_of(self.data.get(self.cfg["dataset"]))
        log, fills = EventLog(), []
        lat = self.cfg.get("latency", 0.0)
        wrap = None

        class Adapter(firm_lobreplay.Strategy):
            def on_market(self, rep, t, snap):
                wrap.market(t, snap)

            def on_fill(self, rep, vid, t, qty, price):
                side = rep.shadows[vid].side
                fills.append((t, side, qty, price))
                wrap.fill(vid, t, qty, price, side)

        rep = firm_lobreplay.Replay(msgs, Adapter(), self.cfg.get("queue", "fifo"), lat, lat)
        back = _Back(rep.send, rep.cancel, lambda: [s.vid for s in rep.working()],
                     lambda: rep.position)
        wrap = _Wrap(self.strategy, _Ctx(back, log))
        res = rep.run()
        return res.pnl(), res.position, fills, log, wrap.mids

    # -- level 4: firm.exchsim, the simulator standing in for the venue
    def _level4(self):
        meta = self.data.meta(self.cfg["dataset"])
        secs, lat = float(meta["seconds"]), int(round(self.cfg.get("latency", 0.0) * 1e9))
        sim = X.Simulator(_venue(secs), seed=self.cfg.get("seed", 1))
        tape = TapeConfig(seconds=secs, seed=int(meta["seed"]), news_at=None)
        sim.add_background(X.TapeBackground(tape))     # the same session, as real orders
        log, fills, side, rctx = EventLog(), [], {}, [None]

        class Inner(firm_lobreplay.Strategy):          # what ReplayStrategyAdapter drives
            def on_market(self, ctx, t, snap):
                rctx[0] = ctx
                wrap.market(t, snap)

            def on_fill(self, ctx, vid, t, qty, price):
                rctx[0] = ctx
                fills.append((t, side[vid], qty, price))
                wrap.fill(vid, t, qty, price, side[vid])

        def send(s, price, qty):
            vid = rctx[0].send(s, price, qty)
            side[vid] = s
            return vid

        back = _Back(send, lambda v: rctx[0].cancel(v), lambda: rctx[0].working(),
                     lambda: rctx[0].position)
        wrap = _Wrap(self.strategy, _Ctx(back, log))
        lm = X.LatencyModel(entry_ns=lat, ack_ns=lat, data_ns=lat)
        sim.add_agent(X.ReplayStrategyAdapter(Inner()), X.SessionSpec("BT", latency=lm))
        sim.run()
        pos = sum(s * q for _, s, q, _ in fills)
        cash = -sum(s * q * p for _, s, q, p in fills)
        mid = wrap.mids[-1][1] if wrap.mids else 0.0
        return cash + pos * mid, pos, fills, log, wrap.mids


def _venue(secs: float) -> X.ExchangeConfig:
    """One continuous session of `secs` seconds from the open, no fees (like the other levels)."""
    o, s = X.OPEN_NS, X.SEC
    ph = X.Phases(start_ns=o - s, open_ns=o, close_ns=o + int(secs) * s, end_ns=o + int(secs + 1) * s)
    return X.ExchangeConfig(phases=ph, fees=X.FeeSchedule(make=0.0, take=0.0))


# ------------------------------------------------------------ results store
class ResultsStore:
    """Runs under root/<run_id>/: manifest.json, fills.parquet, events.parquet. The id is the
    manifest's hash: the same strategy code, engine code, data, parameters and seed give the same id."""

    def __init__(self, root):
        self.root = pathlib.Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, run: Run) -> str:
        d = self.root / run.run_id
        d.mkdir(exist_ok=True)
        (d / "manifest.json").write_text(json.dumps(run.manifest, sort_keys=True, indent=1))
        f, ev = run.fills, run.events
        fills = {"t": f[:, 0], "side": f[:, 1], "qty": f[:, 2], "price": f[:, 3]}
        pq.write_table(pa.table(fills), d / "fills.parquet")
        events = {"t": [e.t for e in ev], "cls": [e.cls for e in ev],
                  "data": [json.dumps(e.data) for e in ev]}
        pq.write_table(pa.table(events), d / "events.parquet")
        return run.run_id

    def load(self, run_id: str) -> dict:
        d = self.root / run_id
        return {"manifest": json.loads((d / "manifest.json").read_text()),
                "fills": pq.read_table(d / "fills.parquet"), "events": pq.read_table(d / "events.parquet")}

    def query(self, **eq) -> list[dict]:
        out = []
        for m in sorted(self.root.glob("*/manifest.json")):
            man = json.loads(m.read_text())
            flat = {**man, **man["params"]}
            if all(flat.get(k) == v for k, v in eq.items()):
                out.append({"run_id": m.parent.name, **flat})
        return out


# ------------------------------------------------------------ comparisons
def first_divergence(a: Run, b: Run, cls: str = "fill"):
    """The first event of class `cls` whose data differ between two runs (the times may differ slightly)."""
    ea = [e for e in a.events if e.cls == cls]
    eb = [e for e in b.events if e.cls == cls]
    for i, (x, y) in enumerate(zip(ea, eb, strict=False)):
        if x.data[1:] != y.data[1:] or abs(x.t - y.t) > 1e-3:
            return i, x, y
    if len(ea) != len(eb):
        i = min(len(ea), len(eb))
        return i, ea[i] if i < len(ea) else None, eb[i] if i < len(eb) else None
    return None


def classify_fills(reactive: Run, replay: Run, tol: float = 1e-3) -> np.ndarray:
    """True for each fill of `reactive` with no fill of the same side in `replay` within `tol` seconds."""
    out = np.ones(len(reactive.fills), dtype=bool)
    for s in (1, -1):
        rt = np.sort(replay.fills[replay.fills[:, 1] == s, 0])
        idx = np.flatnonzero(reactive.fills[:, 1] == s)
        if len(rt) == 0:
            continue
        t = reactive.fills[idx, 0]
        j = np.clip(np.searchsorted(rt, t), 1, len(rt) - 1) if len(rt) > 1 else np.zeros(len(t), int)
        near = np.minimum(np.abs(rt[j] - t), np.abs(rt[np.maximum(j - 1, 0)] - t))
        out[idx] = near > tol
    return out


def markouts(run: Run, horizon: float) -> np.ndarray:
    """Per fill: side x qty x (mid `horizon` seconds after the fill - price), in ticks x shares."""
    if len(run.fills) == 0:
        return np.zeros(0)
    t, s, q, p = run.fills.T
    m = asof(run.mids[:, 0], run.mids[:, 1], t + horizon)
    m = np.where(np.isnan(m), run.mids[-1, 1], m)
    return s * q * (m - p)


def event_queue_demo(events) -> list:
    """The total order of the event model on (t, cls, payload) triples (used by the tests and chapter 12)."""
    h, out = [], []
    for seq, (t, cls, data) in enumerate(events):
        heapq.heappush(h, Event(float(t), RANK[cls], seq, cls, tuple(data)))
    while h:
        out.append(heapq.heappop(h))
    return out
