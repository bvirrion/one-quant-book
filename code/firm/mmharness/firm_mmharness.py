"""firm.mmharness -- the strategy harness of One Quant Book 11 (chapter 1): one Quoter, any market.

Every market-making tutorial of Book 11 writes its strategy once, as a Quoter, and runs it through this harness. Today
the market is Book 7's synthetic message-level market (firm.tape, its agent API: the Quoter's orders are real orders in
the book, matched in price-time priority, seen by the other traders); when Book 10's exchange simulator
(firm.exchsim, INTERFACES.md section 7) lands, an adapter runs the same Quoter there. The harness keeps the Quoter's
view of its own orders (working orders, position, cash, fees), charges the latencies, and returns one Result whose
fill log is the same whatever the market underneath.

Units: prices are integer ticks (the market's tick size converts them to currency); quantities are shares; cash, fees
and P&L are in currency. side = +1 means the Quoter bought, -1 sold. Fees are per share: f_make on passive fills,
f_take on aggressive ones, negative for a rebate (the series' f^make, f^take).

API (stable):
    Latency(data, entry, jitter, seed)        market-data and order-entry latency in seconds, lognormal jitter
    Fees(make, take)                          per share, currency
    Quoter (protocol)                         on_start(ctx); on_market(ctx, t, top); on_fill(ctx, fill);
                                              optional on_timer(ctx, t) every `timer` seconds of market time
    Ctx                                       now, position, cash, fees_paid, messages, top (last seen),
                                              working() -> {cid: Working}, ahead(cid) -> shares ahead in the queue
                                              (Quoters with wants_queue_position = True), send(side, price, qty) -> cid,
                                              last: the message behind the latest update, {kind (b'A', b'X', b'E'),
                                              side (of the resting order), price, qty, agg (+1 buyer-initiated,
                                              -1 seller-initiated, 0)} as an order-by-order feed shows it,
                                              external(top) -> the top of the book without the Quoter's own orders
                                              (exact, as from an order-by-order feed: quoting off one's own orders is
                                              a feedback loop); top also carries the raw bid, ask and sizes,
                                              cancel(cid), take(side, qty) -> cid,
                                              quote(bid, bid_qty, ask, ask_qty, min_move=1): keep one order per side at
                                              the target price, replacing it when the target moves by min_move ticks
                                              or more (None: no order on that side)
    Fill                                      t, cid, side, price, qty, passive
    run_tape(quoter, cfg, latency, fees, v_path=None, timer=None) -> Result
                                              on firm.tape (cfg a firm_tape.TapeConfig; v_path imposes the efficient
                                              price, for common random numbers across Quoters)
    Result                                    fills (FILL structured array), tape, tick, fees, messages, inventory(),
                                              extra['informed']: per fill, whether its aggressor was an informed
                                              trader (evaluation only, never shown to the Quoter),
                                              (t, position after each fill), pnl(ref='mid'), decompose(H, ref) (spread
                                              capture, adverse selection to H, inventory, fees, total; exact, via
                                              firm.markout), markouts(horizons, ref) per fill; ref 'mid' is the
                                              market's mid, 'truth' the efficient price (evaluation only, never shown
                                              to the Quoter, like firm.exchsim's res.truth)
    SymmetricQuoter(size, limit, offset)      joins the best bid and ask (offset ticks behind them), stops adding to a
                                              position beyond `limit` shares: the chapter 1 baseline
"""
from __future__ import annotations

import math
import pathlib
import sys
from dataclasses import dataclass, field

import numpy as np

_HERE = pathlib.Path(__file__).resolve().parent
for _dep in ("tape", "markout"):
    sys.path.insert(0, str(_HERE.parent / _dep))
import firm_markout  # noqa: E402
import firm_tape  # noqa: E402

FILL = np.dtype([("t", "f8"), ("cid", "i8"), ("side", "i1"), ("price", "i8"), ("qty", "i8"), ("passive", "?")])


@dataclass(frozen=True)
class Latency:
    data: float = 0.0005          # seconds from an event to the Quoter seeing it
    entry: float = 0.0005         # seconds from a decision to the order reaching the book
    jitter: float = 0.0           # lognormal sigma of both
    seed: int = 101


@dataclass(frozen=True)
class Fees:
    make: float = 0.0             # currency per share on passive fills (negative: a rebate)
    take: float = 0.0             # currency per share on aggressive fills


@dataclass
class Working:
    side: int
    price: int
    qty: int                      # remaining
    sent: float
    live: float = 0.0             # when it reaches the book (sent + order-entry latency)


@dataclass(frozen=True)
class Fill:
    t: float
    cid: int
    side: int
    price: int
    qty: int
    passive: bool


class Ctx:
    """The Quoter's view of the market and of its own orders. Actions are queued and delivered after the order-entry
    latency by the adapter; a cancelled order can still fill while the cancel travels (the race is real)."""

    def __init__(self, tick: float, fees: Fees, entry: float = 0.0):
        self.tick, self.fee_sched, self.entry = tick, fees, entry
        self.now = 0.0
        self.position = 0
        self.cash = 0.0
        self.fees_paid = 0.0
        self.messages = 0
        self.top = None
        self._working: dict[int, Working] = {}
        self._ahead: dict[int, int] = {}
        self.last = None
        self._next = 0
        self._out: list = []

    def working(self) -> dict[int, Working]:
        return dict(self._working)

    def ahead(self, cid: int):
        """Shares ahead of the order in its queue as of the last market update (None if unknown or not resting yet).
        Published only to Quoters with the attribute wants_queue_position = True."""
        return self._ahead.get(cid)

    def send(self, side: int, price: int, qty: int) -> int:
        self._next += 1
        self._working[self._next] = Working(side, int(price), int(qty), self.now, self.now + self.entry)
        self._out.append(("limit", self._next, side, int(price), int(qty)))
        self.messages += 1
        return self._next

    def cancel(self, cid: int) -> None:
        if self._working.pop(cid, None) is not None:
            self._out.append(("cancel", cid))
            self.messages += 1

    def take(self, side: int, qty: int) -> int:
        self._next += 1
        self._out.append(("market", self._next, side, int(qty)))
        self.messages += 1
        return self._next

    def external(self, top) -> dict:
        """The top of the book without the Quoter's own orders (xbid, xbid_qty, xask, xask_qty in the market's top):
        a market maker reading an order-by-order feed knows its own order ids, so this is exact."""
        return {"t": top["t"], "bid": top["xbid"], "bid_qty": top["xbid_qty"], "ask": top["xask"],
                "ask_qty": top["xask_qty"]}

    def quote(self, bid, bid_qty, ask, ask_qty, min_move: int = 1) -> None:
        for side, px, qty in ((1, bid, bid_qty), (-1, ask, ask_qty)):
            mine = [(c, w) for c, w in self._working.items() if w.side == side]
            if px is None or qty <= 0:
                for c, _ in mine:
                    self.cancel(c)
                continue
            keep = [c for c, w in mine if abs(w.price - px) < min_move]
            for c, _ in mine:
                if c not in keep[:1]:
                    self.cancel(c)
            if not keep:
                self.send(side, int(px), int(qty))

    def _fill(self, f: Fill) -> None:
        w = self._working.get(f.cid)
        if w is not None:
            w.qty -= f.qty
            if w.qty <= 0:
                del self._working[f.cid]
        self.position += f.side * f.qty
        self.cash -= f.side * f.qty * f.price * self.tick
        fee = (self.fee_sched.make if f.passive else self.fee_sched.take) * f.qty
        self.fees_paid += fee
        self.cash -= fee

    def _drain(self) -> list:
        out, self._out = self._out, []
        return out


class SymmetricQuoter:
    """Join the best bid and ask with `size` shares (or `offset` ticks behind them); stop quoting the side that would
    take the position beyond `limit` shares. The baseline market maker of chapter 1. raw=True quotes off the raw top,
    own orders included: the feedback loop the harness exists to prevent (kept to show it)."""

    def __init__(self, size: int = 100, limit: int = 1000, offset: int = 0, raw: bool = False):
        self.size, self.limit, self.offset, self.raw = size, limit, offset, raw

    def on_start(self, ctx: Ctx) -> None:
        pass

    def on_market(self, ctx: Ctx, t: float, top) -> None:
        ext = top if self.raw else ctx.external(top)
        bid, ask = int(ext["bid"]) - self.offset, int(ext["ask"]) + self.offset
        bq = self.size if ctx.position + self.size <= self.limit else 0
        aq = self.size if ctx.position - self.size >= -self.limit else 0
        ctx.quote(bid, bq, ask, aq)

    def on_fill(self, ctx: Ctx, fill: Fill) -> None:
        pass


class _TapeAgent:
    """Adapter: a Quoter as a firm.tape agent (delay_data, delay_entry, on_market, on_fill)."""

    def __init__(self, quoter, ctx: Ctx, latency: Latency, timer: float | None):
        self.q, self.ctx, self.lat, self.timer = quoter, ctx, latency, timer
        self.want_ahead = bool(getattr(quoter, "wants_queue_position", False))
        self.rng = np.random.default_rng(latency.seed)
        self.next_timer = timer if timer else math.inf
        self.fills: list = []
        self.started = False

    def _draw(self, base: float) -> float:
        if self.lat.jitter <= 0:
            return base
        return base * float(np.exp(self.lat.jitter * self.rng.standard_normal() - 0.5 * self.lat.jitter**2))

    def delay_data(self) -> float:
        return self._draw(self.lat.data)

    def delay_entry(self) -> float:
        return self._draw(self.lat.entry)

    def on_market(self, t, payload):
        top, x, ahead, msg = payload
        self.ctx._ahead = ahead or {}
        self.ctx.last = {"kind": msg[0], "side": msg[1], "price": msg[2], "qty": msg[3], "agg": msg[4]}
        c = self.ctx
        c.now, c.top = t, {"t": top[0], "bid": top[1], "bid_qty": top[2], "ask": top[3], "ask_qty": top[4],
                           "xbid": x[0], "xbid_qty": x[1], "xask": x[2], "xask_qty": x[3]}
        if not self.started:
            self.started = True
            self.q.on_start(c)
        while t >= self.next_timer:
            if hasattr(self.q, "on_timer"):
                self.q.on_timer(c, self.next_timer)
            self.next_timer += self.timer
        self.q.on_market(c, t, c.top)
        return c._drain()

    def on_fill(self, t, cid, side, price, qty, passive):
        c = self.ctx
        c.now = t
        f = Fill(float(t), int(cid), int(side), int(price), int(qty), bool(passive))
        c._fill(f)
        self.fills.append((f.t, f.cid, f.side, f.price, f.qty, f.passive))
        self.q.on_fill(c, f)
        return c._drain()


class _HarnessSim(firm_tape._Sim):
    """firm.tape's simulator publishing, with every top of book, the top without the agent's own orders (what an
    order-by-order feed gives a firm that knows its order ids). The market itself is unchanged."""

    def _ext(self, side: int, px: int, qty: int, own_rest):
        mine = sum(e[1] for o, e in own_rest.items() if self.where[o] == (side, px))
        if mine < qty:
            return px, qty - mine                            # others remain at the touch
        lv = self.book[side]
        for p in sorted(lv, reverse=(side == 1)):
            q = sum(o[1] for o in lv[p] if o[0] not in self.own)
            if q > 0:
                return p, q
        return (min(lv) - 1 if side == 1 else max(lv) + 1), 0

    def _emit(self, t, kind, oid, side, px, qty, agg, trade):
        self.msgs.append((t, kind, oid, side, px, qty, agg, trade))
        if not self.seeding:
            top = self._top(t)
            self.top.append(top)
            if self.agent is not None:
                own_rest = self.__dict__.setdefault("_own_rest", {})
                if kind == b"A" and oid in self.own:           # keep the book entry [oid, qty], updated in place
                    own_rest[oid] = self.book[side][px][-1]
                for o in [o for o in own_rest if o not in self.where]:
                    del own_rest[o]
                xb, xa = self._ext(1, top[1], top[2], own_rest), self._ext(-1, top[3], top[4], own_rest)
                ahead = self._ahead(own_rest) if self.agent.want_ahead else None
                msg = (kind, side, px, qty, agg)
                self._apush(t + self.agent.delay_data(), 0, (top, (xb[0], xb[1], xa[0], xa[1]), ahead, msg))

    def _market(self, t, sign, qty, informed):
        self._informed = informed                           # the aggressor's class, for the evaluation-only log
        super()._market(t, sign, qty, informed)

    def _agent_fill(self, t, cid, side, px, qty, passive):
        self.__dict__.setdefault("_fill_class", []).append(bool(self._informed) if passive else False)
        super()._agent_fill(t, cid, side, px, qty, passive)

    def _ahead(self, own_rest) -> dict:
        """{client id: shares ahead in the queue} for every resting own order (as an order-by-order feed shows it)."""
        out = {}
        for o in own_rest:
            side, px = self.where[o]
            n = 0
            for oid, q in self.book[side][px]:
                if oid == o:
                    break
                n += q
            out[self.own[o]] = n
        return out


@dataclass
class Result:
    fills: np.ndarray
    tape: object
    tick: float
    fees: Fees
    messages: int
    fees_paid: float
    extra: dict = field(default_factory=dict)

    def _ref(self, ref: str):
        tp = self.tape
        if ref == "truth":
            return np.asarray(tp.v_t, float), np.asarray(tp.v, float)
        top = tp.top[tp.n_open - 1:]
        return top["t"].astype(float), 0.5 * (top["bid"] + top["ask"]).astype(float)

    def inventory(self) -> tuple[np.ndarray, np.ndarray]:
        f = self.fills
        return f["t"], np.cumsum(f["side"].astype(np.int64) * f["qty"])

    def volume(self) -> int:
        return int(self.fills["qty"].sum())

    def pnl(self, ref: str = "mid") -> float:
        rt, rp = self._ref(ref)
        f = self.fills
        pos = int((f["side"].astype(np.int64) * f["qty"]).sum())
        cash = -float((f["side"] * f["qty"] * f["price"]).sum()) * self.tick
        return cash + pos * float(rp[-1]) * self.tick - self.fees_paid

    def decompose(self, H: float, ref: str = "mid") -> dict:
        """Spread capture, adverse selection up to H seconds, inventory after H, fees; in currency; exact."""
        rt, rp = self._ref(ref)
        f = self.fills
        T = float(self.tape.cfg.seconds)
        if len(f) == 0:
            return {"spread": 0.0, "adverse": 0.0, "inventory": 0.0, "fees": 0.0, "total": 0.0}
        d = firm_markout.mm_decompose(f["t"], f["side"], f["price"], f["qty"], rt, rp, H, 0.0, T)
        out = {k: v * self.tick for k, v in d.items() if k != "fees"}
        out["fees"] = -self.fees_paid
        out["total"] = out["spread"] + out["adverse"] + out["inventory"] + out["fees"]
        return out

    def markouts(self, horizons, ref: str = "mid") -> np.ndarray:
        """Per fill and horizon: side * (ref(t + h) - price), in ticks per share."""
        rt, rp = self._ref(ref)
        f = self.fills
        return firm_markout.markouts(f["t"], f["side"], f["price"], rt, rp, horizons)


def run_tape(quoter, cfg=None, latency: Latency | None = None, fees: Fees | None = None, v_path=None,
             timer: float | None = None) -> Result:
    """Run one Quoter inside firm.tape's synthetic market for cfg.seconds."""
    cfg = cfg or firm_tape.TapeConfig()
    latency, fees = latency or Latency(), fees or Fees()
    ctx = Ctx(cfg.tick, fees, latency.entry)
    agent = _TapeAgent(quoter, ctx, latency, timer)
    sim = _HarnessSim(cfg, v_path, agent)
    tape = sim.run()
    fills = np.array(agent.fills, dtype=FILL)
    extra = {"informed": np.array(sim.__dict__.get("_fill_class", []), bool)}
    return Result(fills, tape, cfg.tick, fees, ctx.messages, ctx.fees_paid, extra)


def common_path(cfg=None):
    """The efficient-price path (times, values, activity) of cfg, to run several Quoters on the same market."""
    cfg = cfg or firm_tape.TapeConfig()
    rng = np.random.default_rng(cfg.seed)
    act = firm_tape.activity(cfg, rng)
    vt, v = firm_tape.efficient_path(cfg, rng, act)
    return vt, v, act
