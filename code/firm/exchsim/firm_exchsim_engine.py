"""firm.exchsim engine -- the deterministic matching engine (build of One Quant Book 10, chapter 26).

The engine is a pure function of its journal: records (t_ns, session, message) in arrival order, session 0 carrying
the operator's control messages. For each record it produces feed messages (in order) and execution reports to
sessions (in order), all stamped with the time the engine finished the record: start = max(t_ns, busy_until),
stamp = start + engine_ns. The C++20 (cpp/exchsim_engine.hpp) and Rust (rust/src/engine.rs) engines implement the
same rules and must produce byte-identical outputs on the shared fixtures; PROTOCOL.md states every rule.

Rules in the order the engine applies them (continuous trading):
  1. throttle (token bucket per session, integer nano-tokens) -> J T
  2. validation (firm.ordertypes.validate), duplicates -> J D, post-only -> J O
  3. Accepted (A); a stop order waits (state S)
  4. fill-or-kill and minimum-quantity checks on the executable quantity -> C I
  5. matching: price priority over the opposite side (within the band), then the level's allocation: FIFO over
     displayed then hidden orders, or firm_match.configurable (top order share, FIFO share, pro rata, leftovers by
     time); self-trade prevention by the incoming order's mode; resting orders with min_qty above the incoming
     remainder are skipped; an iceberg whose shown slice is consumed refreshes at the back with a new reference
  6. the remainder: market, IOC and FOK are cancelled (C I); others rest (A on the feed if visible)
  7. settle: triggered stops enter, pegs move (a midpoint peg prices off the reference quote of control N when one
     has been received: a dark venue), and a crossed book (after an auction, a peg move) is uncrossed by
     treating the later of the two top orders as the aggressor; repeated until nothing changes
Call phases (opening, closing, paused, batch) accept orders without matching; leaving a call phase, or a batch
uncross, runs Book 1's firm_auction rules (maximum volume, minimum surplus, market pressure, reference price).

API (stable):
    Engine(config: dict)                          config as ExchangeConfig.engine_config() writes it (JSON-able)
    Engine.process(t_ns, session, msg) -> (feed, reports)     msg a codec namedtuple (In_* or Ctl_*); feed a list
                                                  of Feed_* namedtuples, reports a list of (session, Out_*)
    Engine.process_bytes(t_ns, session, payload)  the same from raw bytes (session 0: ctl protocol)
    Engine.snapshot(locate) -> list[Feed_*]       G, H, the displayed orders (A) in priority order, W with CRC32
    Engine.trades                                 (match, locate, price, qty, resting session, aggressor session,
                                                   aggressor side, liquidity) for every execution: evaluation only
    Engine.book(locate), Engine.phase(locate)     read-only views for the simulator
    fee(config, liquidity, price, qty)            integer fee in 1e-6 currency units (negative = rebate)
"""
from __future__ import annotations

import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
for _c in ("lob", "ordertypes", "match", "auction"):
    sys.path.insert(0, str(_HERE.parent / _c))
from firm_auction import AuctionOrder, uncross  # noqa: E402
from firm_exchsim_codec import NT, crc32, decode, encode  # noqa: E402
from firm_lob import LimitOrderBook  # noqa: E402
from firm_match import Resting, configurable  # noqa: E402
from firm_ordertypes import (  # noqa: E402
    CALL_PHASES,
    MAX_QTY,
    EOrder,
    marketable,
    peg_target,
    slice_for_display,
    stop_triggered,
    stp_actions,
    stp_conflict,
    validate,
)

F, OUT = NT["feed"], NT["out"]
NANO = 1_000_000_000
STATE = {"T": "T", "H": "H", "U": "P", "O": "Q", "K": "Q", "B": "Q", "C": "C"}
CROSS_OF_CALL = {"O": "O", "K": "C", "U": "H", "B": "B"}


def _trunc_div(a: int, b: int) -> int:
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def fee(cfg: dict, liquidity: str, price: int, qty: int) -> int:
    f = cfg["fees"]
    rate = {"A": f["make"], "R": f["take"], "C": f["cross"]}[liquidity]
    if f["unit"] == "share":
        return rate * qty
    return _trunc_div(price * qty * rate, 10_000)


class _Inst:
    __slots__ = ("locate", "symbol", "tick", "lot", "matching", "top_pct", "fifo_pct", "min_alloc", "book", "phase",
                 "ref_price", "band", "last", "frozen", "stops", "mkt", "close", "pegs", "pegged", "ref_quote")

    def __init__(self, d: dict):
        self.locate, self.symbol, self.tick, self.lot = d["locate"], d["symbol"], d["tick"], d["lot"]
        self.matching = d.get("matching", "F")
        self.top_pct, self.fifo_pct, self.min_alloc = d.get("top_pct", 0), d.get("fifo_pct", 0), d.get("min_alloc", 1)
        self.book = LimitOrderBook()
        self.phase = d.get("phase", "C")
        self.ref_price = d.get("start_price", 0)
        self.band = (0, 0)
        self.last = 0
        self.frozen = False
        self.stops: list[EOrder] = []
        self.mkt: list[EOrder] = []
        self.close: list[EOrder] = []
        self.pegs: list[EOrder] = []
        self.pegged: set[int] = set()
        self.ref_quote: tuple[int, int] | None = None       # external reference (control N) for midpoint pegs


class _Sess:
    __slots__ = ("firm", "cod", "logged", "tokens", "last_t", "used", "live", "quotes")

    def __init__(self, firm: int, cod: bool, burst: int):
        self.firm, self.cod, self.logged = firm, cod, True
        self.tokens, self.last_t = burst * NANO, None
        self.used: set[int] = set()
        self.live: dict[int, EOrder] = {}
        self.quotes: dict[int, tuple[int, int]] = {}


class Engine:
    def __init__(self, config: dict):
        self.cfg = config
        self.engine_ns = config.get("engine_ns", 0)
        th = config.get("throttle", {"rate": 0, "burst": 0})
        self.rate, self.burst, self.weights = th["rate"], th["burst"], th.get("weights", {})
        self.inst = {d["locate"]: _Inst(d) for d in config["instruments"]}
        self.sessions: dict[int, _Sess] = {}
        self.busy, self.ts = 0, 0
        self.next_ref, self.next_match, self.seq = 1, 0, 0
        self.trades: list[tuple] = []
        self._feed: list = []
        self._rep: list = []
        self._touched: set[int] = set()

    # -- public ----------------------------------------------------------------------------------------------------
    def book(self, locate: int) -> LimitOrderBook:
        return self.inst[locate].book

    def phase(self, locate: int) -> str:
        return self.inst[locate].phase

    def process_bytes(self, t_ns: int, session: int, payload: bytes):
        return self.process(t_ns, session, decode("ctl" if session == 0 else "in", payload))

    def process(self, t_ns: int, session: int, msg):
        self.ts = max(t_ns, self.busy) + self.engine_ns
        self.busy = self.ts
        self._feed, self._rep, self._touched = [], [], set()
        name = type(msg).__name__
        if session == 0:
            getattr(self, "_ctl_" + name[-1])(msg)
        else:
            s = self.sessions.get(session)
            if s is not None and s.logged:
                if self._throttled(s, t_ns, self.weights.get(name[-1], 1)):
                    self._rep.append((session, OUT["J"](self.ts, _msg_cl(msg), "T")))
                else:
                    getattr(self, "_in_" + name[-1])(session, s, msg)
        for loc in sorted(self._touched):
            self._settle(self.inst[loc])
        return self._feed, self._rep

    def snapshot(self, locate: int, seq: int = 0, ts: int | None = None) -> list:
        """The displayed book in priority order, framed by G (with the incremental seq it reflects) and W (CRC32 of
        the encoded A messages)."""
        st, ts = self.inst[locate], self.ts if ts is None else ts
        out = [F["G"](locate, 0, ts, seq, len([o for o in st.book.orders.values() if o.visible])),
               F["H"](locate, 0, ts, st.symbol, STATE[st.phase], " ", "SNAP")]
        body = b""
        for side in (1, -1):
            for p in st.book.prices(side):
                for o in st.book.level_orders(side, p):
                    if o.visible:
                        a = F["A"](locate, 0, ts, o.ref, "B" if side == 1 else "S", o.qty, st.symbol, p)
                        body += encode("feed", a)
                        out.append(a)
        out.append(F["W"](locate, 0, ts, seq, crc32(body)))
        return out

    # -- helpers ---------------------------------------------------------------------------------------------------
    def _throttled(self, s: _Sess, t: int, weight: int = 1) -> bool:
        if self.rate <= 0:
            return False
        cap = self.burst * NANO
        if s.last_t is not None:
            s.tokens = min(cap, s.tokens + (t - s.last_t) * self.rate)
        s.last_t = t
        if s.tokens >= weight * NANO:
            s.tokens -= weight * NANO
            return False
        return True

    def _new_ref(self) -> int:
        r = self.next_ref
        self.next_ref += 1
        return r

    def _next_seq(self) -> int:
        self.seq += 1
        return self.seq

    def _rep_to(self, session: int, msg) -> None:
        self._rep.append((session, msg))

    def _done(self, o: EOrder) -> None:
        o.where = ""
        live = self.sessions[o.session].live
        if live.get(o.cl) is o:
            del live[o.cl]
        pegs = self.inst[o.locate].pegs
        if o in pegs:
            pegs.remove(o)

    def _remove_from_container(self, st: _Inst, o: EOrder, publish: bool = True) -> None:
        if o.where == "book":
            st.book.remove(o.ref)
            st.pegged.discard(o.ref)
            if publish and o.visible:
                self._feed.append(F["D"](st.locate, 0, self.ts, o.ref))
        elif o.where == "stop":
            st.stops.remove(o)
        elif o.where == "mkt":
            st.mkt.remove(o)
        elif o.where == "close":
            st.close.remove(o)
        o.where = ""

    def _cancel(self, o: EOrder, reason: str) -> None:
        st = self.inst[o.locate]
        d = o.remaining
        self._remove_from_container(st, o)
        self._rep_to(o.session, OUT["C"](self.ts, o.cl, d, reason))
        self._done(o)
        self._touched.add(st.locate)

    def _decrement(self, o: EOrder, d: int, reason: str) -> None:
        """Take d off the order: the reserve first, then the shown slice (X on the feed if visible)."""
        st = self.inst[o.locate]
        if d >= o.remaining:
            self._cancel(o, reason)
            return
        from_res = min(o.reserve, d)
        o.reserve -= from_res
        shown = d - from_res
        if shown:
            if o.where == "book":
                st.book.reduce(o.ref, shown)
                if o.visible:
                    self._feed.append(F["X"](st.locate, 0, self.ts, o.ref, shown))
            else:
                o.qty -= shown
        self._rep_to(o.session, OUT["C"](self.ts, o.cl, d, reason))
        self._touched.add(st.locate)

    def _rest(self, st: _Inst, o: EOrder, rem: int) -> None:
        """Put the unexecuted remainder of an incoming order in the book (A on the feed if visible)."""
        shown, reserve = slice_for_display(o, rem)
        o.qty, o.reserve = shown, reserve
        best = st.book.best(o.side)
        o.top = best is None or (o.price > best if o.side == 1 else o.price < best)
        st.book.add(o)
        o.where = "book"
        if o.display in "MP":
            st.pegged.add(o.ref)
        if o.visible:
            self._feed.append(F["A"](st.locate, 0, self.ts, o.ref, "B" if o.side == 1 else "S", shown, st.symbol,
                                     o.price))

    # -- matching --------------------------------------------------------------------------------------------------
    def _eligible(self, st: _Inst, o: EOrder, lim: int, rem: int) -> int:
        """Executable quantity for an incoming order (for FOK and minimum quantity), ignoring self-trades."""
        total = 0
        lo, hi = st.band
        for p in st.book.prices(-o.side):
            if not marketable(o.side, lim, p) or (hi and not lo <= p <= hi):
                break
            for r in st.book.level_orders(-o.side, p):
                if stp_conflict(o, r) or (r.min_qty and rem < r.min_qty):
                    continue
                total += r.remaining
        return total

    def _execute(self, st: _Inst, r: EOrder, o: EOrder, q: int, p: int, rem_after: int) -> None:
        self.next_match += 1
        m = self.next_match
        if r.visible:
            self._feed.append(F["E"](st.locate, 0, self.ts, r.ref, q, m))
        else:
            self._feed.append(F["P"](st.locate, 0, self.ts, 0, "B" if r.side == 1 else "S", q, st.symbol, p, m))
        st.book.reduce(r.ref, q)
        if r.qty == 0:
            st.pegged.discard(r.ref)
            if r.reserve > 0:                      # an iceberg refreshes at the back, under a new reference
                shown = min(r.display_qty, r.reserve)
                r.reserve -= shown
                r.qty, r.ref, r.seq, r.top = shown, self._new_ref(), self._next_seq(), False
                st.book.add(r)
                self._feed.append(F["A"](st.locate, 0, self.ts, r.ref, "B" if r.side == 1 else "S", shown,
                                         st.symbol, r.price))
            else:
                r.where = ""
        self._rep_to(r.session, OUT["E"](self.ts, r.cl, q, p, m, "A", fee(self.cfg, "A", p, q), r.remaining))
        if r.remaining == 0:
            self._done(r)
        self._rep_to(o.session, OUT["E"](self.ts, o.cl, q, p, m, "R", fee(self.cfg, "R", p, q), rem_after))
        st.last = p
        self.trades.append((m, st.locate, p, q, r.session, o.session, o.side, "R", o.cl))

    def _match(self, st: _Inst, o: EOrder, lim: int, rem: int) -> int:
        """Execute an incoming order against the opposite side; return what is left (0 if cancelled by STP)."""
        opp = -o.side
        lo, hi = st.band
        for p in st.book.prices(opp):
            if rem == 0 or not marketable(o.side, lim, p) or (hi and not lo <= p <= hi):
                break
            while rem > 0:
                level = st.book.level_orders(opp, p)
                if not level:
                    break
                elig = []
                for r in level:
                    if stp_conflict(o, r) and o.stp_mode != "N":
                        cr, ci, dec = stp_actions(o.stp_mode)
                        if dec:
                            d = min(rem, r.remaining)
                            self._decrement(r, d, "S")
                            rem -= d
                            self._rep_to(o.session, OUT["C"](self.ts, o.cl, d, "S"))
                            if rem == 0:
                                return 0
                            continue
                        if cr:
                            self._cancel(r, "S")
                        if ci:
                            self._rep_to(o.session, OUT["C"](self.ts, o.cl, rem, "S"))
                            return -1
                        continue
                    if r.min_qty and rem < r.min_qty:
                        continue
                    elig.append(r)
                if not elig:
                    if len(st.book.level_orders(opp, p)) == len(level):
                        break                      # nothing executable: next price
                    continue                       # STP removed some: look again
                if st.matching == "F":
                    alloc = []
                    left = rem
                    for r in elig:
                        f = min(r.qty, left)
                        alloc.append((r, f))
                        left -= f
                        if left == 0:
                            break
                else:
                    book = [Resting(str(i), r.qty, False, r.top) for i, r in enumerate(elig)]
                    got = configurable(book, rem, st.top_pct, 0, st.fifo_pct, st.min_alloc)
                    alloc = [(r, got.get(str(i), 0)) for i, r in enumerate(elig)]
                for r, f in alloc:
                    if f > 0:
                        rem -= f
                        self._execute(st, r, o, f, p, rem)
        return rem

    def _incoming(self, st: _Inst, o: EOrder, lim: int, rem: int) -> None:
        """Continuous trading: FOK/min-qty checks, matching, then rest or cancel the remainder."""
        need = rem if o.tif == "F" else o.min_qty
        if need and self._eligible(st, o, lim, rem) < need:
            if o.tif in "IF":
                self._rep_to(o.session, OUT["C"](self.ts, o.cl, rem, "I"))
                self._done(o)
            else:                                  # a midpoint peg below its minimum rests without trading
                o.price = lim
                self._rest(st, o, rem)
            return
        rem = self._match(st, o, lim, rem)
        if rem < 0 or rem == 0:
            if rem == 0:
                o.qty, o.reserve = 0, 0
            self._done(o)
            return
        if lim == 0 or o.tif in "IF":
            self._rep_to(o.session, OUT["C"](self.ts, o.cl, rem, "I"))
            self._done(o)
            return
        o.price = lim
        self._rest(st, o, rem)

    # -- order entry -----------------------------------------------------------------------------------------------
    def _accept(self, session: int, s: _Sess, m, st: _Inst) -> EOrder:
        o = EOrder(self._new_ref(), 1 if m.side == "B" else -1, m.price, m.qty, cl=m.cl_ord_id, session=session,
                   firm=s.firm, locate=m.locate, tif=m.tif, display=m.display, post_only=m.post_only == "Y",
                   display_qty=m.display_qty, min_qty=m.min_qty, stp_group=m.stp_group, stp_mode=m.stp_mode,
                   stop_price=m.stop_price, limit=m.price, seq=self._next_seq())
        s.used.add(m.cl_ord_id)
        s.live[m.cl_ord_id] = o
        self._rep_to(session, OUT["A"](self.ts, m.cl_ord_id, o.ref, m.locate, m.side, m.qty, m.price, m.tif,
                                     m.display, "S" if m.stop_price else "L"))
        return o

    def _would_cross(self, st: _Inst, side: int, lim: int) -> bool:
        p = st.book.best(-side)
        return p is not None and marketable(side, lim, p)

    def _enter(self, session: int, s: _Sess, m) -> None:
        st = self.inst.get(m.locate)
        if st is None:
            self._rep_to(session, OUT["J"](self.ts, m.cl_ord_id, "S"))
            return
        if m.cl_ord_id in s.used:
            self._rep_to(session, OUT["J"](self.ts, m.cl_ord_id, "D"))
            return
        why = validate(m, st, st.phase, st.frozen, st.band)
        if (why is None and m.post_only == "Y" and st.phase == "T" and not m.stop_price and m.display in "YN"
                and self._would_cross(st, 1 if m.side == "B" else -1, m.price)):
            why = "O"
        if why is not None:
            self._rep_to(session, OUT["J"](self.ts, m.cl_ord_id, why))
            return
        self._touched.add(st.locate)
        o = self._accept(session, s, m, st)
        if m.stop_price:
            o.where = "stop"
            st.stops.append(o)
            return
        if m.tif == "C":
            o.where = "close"
            st.close.append(o)
            return
        if m.display in "MP":
            st.pegs.append(o)
            o.where = "peg"                        # settle() prices and activates it
            return
        if st.phase in CALL_PHASES:
            self._to_call(st, o)
            return
        self._incoming(st, o, o.limit, o.qty)

    def _to_call(self, st: _Inst, o: EOrder) -> None:
        if o.tif in "IF":
            self._rep_to(o.session, OUT["C"](self.ts, o.cl, o.remaining, "I"))
            self._done(o)
        elif o.limit == 0:
            o.where = "mkt"
            st.mkt.append(o)
        else:
            o.price = o.limit
            self._rest(st, o, o.remaining)

    def _in_O(self, session, s, m):
        self._enter(session, s, m)

    def _in_X(self, session, s, m):
        o = s.live.get(m.cl_ord_id)
        if o is None:
            self._rep_to(session, OUT["J"](self.ts, m.cl_ord_id, "L"))
            return
        if m.leave_qty >= o.remaining:
            return
        if m.leave_qty == 0:
            self._cancel(o, "U")
        else:
            self._decrement(o, o.remaining - m.leave_qty, "U")

    def _in_M(self, session, s, m):
        side = {"B": 1, "S": -1}.get(m.side, 0)
        for o in sorted(s.live.values(), key=lambda x: x.seq):
            if (m.locate == 0 or o.locate == m.locate) and (side == 0 or o.side == side):
                self._cancel(o, "M")

    def _in_U(self, session, s, m):
        o = s.live.get(m.cl_ord_id)
        if o is None:
            self._rep_to(session, OUT["J"](self.ts, m.cl_ord_id, "L"))
            return
        st = self.inst[o.locate]
        if m.new_cl_ord_id in s.used:
            self._rep_to(session, OUT["J"](self.ts, m.new_cl_ord_id, "D"))
            return
        why = None
        if st.phase in "CH":
            why = "H"
        elif m.qty <= 0 or m.qty > MAX_QTY:
            why = "Q"
        elif m.price % st.tick or (m.price == 0) != (o.limit == 0):
            why = "X"
        elif m.price and st.band[1] and not st.band[0] <= m.price <= st.band[1]:
            why = "B"
        elif (o.post_only and st.phase == "T" and o.where == "book" and o.display not in "MP"
              and (m.price != o.limit) and self._would_cross(st, o.side, m.price)):
            why = "O"
        if why is not None:
            self._rep_to(session, OUT["J"](self.ts, m.new_cl_ord_id, why))
            return
        self._touched.add(st.locate)
        s.used.add(m.new_cl_ord_id)
        del s.live[o.cl]
        old_cl, o.cl = o.cl, m.new_cl_ord_id
        s.live[o.cl] = o
        if m.price == o.limit and m.qty <= o.remaining and o.where in ("book", "stop", "mkt", "close", "peg"):
            d = o.remaining - m.qty
            if d:
                from_res = min(o.reserve, d)
                o.reserve -= from_res
                shown = d - from_res
                if shown:
                    if o.where == "book":
                        st.book.reduce(o.ref, shown)
                        if o.visible:
                            self._feed.append(F["X"](st.locate, 0, self.ts, o.ref, shown))
                    else:
                        o.qty -= shown
            self._rep_to(session, OUT["U"](self.ts, old_cl, o.cl, o.ref, m.qty, m.price, "Y"))
            return
        was_book, vis, old_ref = o.where == "book", o.visible, o.ref
        if o.where == "book":
            st.book.remove(o.ref)
            st.pegged.discard(o.ref)
            o.where = ""
        o.limit, o.seq = m.price, self._next_seq()
        o.qty, o.reserve = m.qty, 0
        if was_book:
            o.ref = self._new_ref()
        self._rep_to(session, OUT["U"](self.ts, old_cl, o.cl, o.ref, m.qty, m.price, "N"))
        if not was_book:                           # stop, market-in-call, at-close or inactive peg: updated in place
            return
        if o.display in "MP":
            if vis:
                self._feed.append(F["D"](st.locate, 0, self.ts, old_ref))
            o.where = "peg"
            return
        if st.phase == "T" and self._would_cross(st, o.side, o.limit):
            if vis:
                self._feed.append(F["D"](st.locate, 0, self.ts, old_ref))
            self._incoming(st, o, o.limit, o.qty)
            return
        o.price = o.limit
        shown, reserve = slice_for_display(o, o.qty)
        o.qty, o.reserve, o.top = shown, reserve, False
        st.book.add(o)
        o.where = "book"
        if vis:
            self._feed.append(F["U"](st.locate, 0, self.ts, old_ref, o.ref, shown, o.price))

    def _in_Q(self, session, s, m):
        st = self.inst.get(m.locate)
        legs = ((m.quote_id * 2, "B", m.bid_price, m.bid_qty), (m.quote_id * 2 + 1, "S", m.ask_price, m.ask_qty))
        if st is None:
            self._rep_to(session, OUT["J"](self.ts, legs[0][0], "S"))
            return
        for cl in s.quotes.pop(m.locate, ()):
            o = s.live.get(cl)
            if o is not None:
                self._cancel(o, "U")
        ids = []
        for cl, side, px, qty in legs:
            if qty == 0:
                continue
            ids.append(cl)
            self._enter(session, s, NT["in"]["O"](cl, m.locate, side, qty, px, "D", "Y", "N", 0, 0, 0, "N", 0))
        s.quotes[m.locate] = tuple(ids)

    # -- settle: stops, pegs, crossed books ---------------------------------------------------------------------
    def _settle(self, st: _Inst) -> None:
        stuck = False
        for _ in range(64):
            changed = False
            if st.phase == "T":
                trig = [o for o in st.stops if stop_triggered(o, st.last)]
                for o in trig:
                    if o.where != "stop":
                        continue
                    st.stops.remove(o)
                    o.where = ""
                    o.stop_price = 0
                    if o.display in "MP":
                        st.pegs.append(o)
                        o.where = "peg"
                    else:
                        self._incoming(st, o, o.limit, o.qty)
                    changed = True
                for o in list(st.pegs):
                    if o.where not in ("book", "peg"):
                        continue
                    target = peg_target(o, st.book, st.pegged, st.ref_quote)
                    if o.where == "book" and target == o.price:
                        continue
                    if o.where == "peg" and target is None:
                        continue
                    changed = True
                    old_ref, vis = o.ref, o.visible
                    if o.where == "book":
                        st.book.remove(o.ref)
                        st.pegged.discard(o.ref)
                        rem = o.remaining
                        o.qty, o.reserve = rem, 0
                        if target is None:
                            o.where = "peg"
                            if vis:
                                self._feed.append(F["D"](st.locate, 0, self.ts, old_ref))
                            continue
                        o.where = ""
                        if self._would_cross(st, o.side, target):
                            if vis:
                                self._feed.append(F["D"](st.locate, 0, self.ts, old_ref))
                            o.ref = self._new_ref() if vis else o.ref
                            self._incoming(st, o, target, rem)
                            continue
                        o.price, o.top = target, False
                        if vis:
                            o.ref = self._new_ref()
                        st.book.add(o)
                        st.pegged.add(o.ref)
                        o.where = "book"
                        if vis:
                            self._feed.append(F["U"](st.locate, 0, self.ts, old_ref, o.ref, o.qty, o.price))
                    else:                           # an inactive peg becomes active
                        o.where = ""
                        self._incoming(st, o, target, o.qty)
                b, a = st.book.best(1), st.book.best(-1)
                if b is not None and a is not None and b >= a and not stuck:
                    before = len(self.trades)
                    rb, ra = st.book.level_orders(1, b)[0], st.book.level_orders(-1, a)[0]
                    agg = rb if rb.seq > ra.seq else ra
                    rem = agg.remaining
                    st.book.remove(agg.ref)
                    st.pegged.discard(agg.ref)
                    if agg.visible:
                        self._feed.append(F["D"](st.locate, 0, self.ts, agg.ref))
                        agg.ref = self._new_ref()
                    agg.qty, agg.reserve, agg.where = rem, 0, ""
                    self._incoming(st, agg, agg.price, rem)
                    if len(self.trades) == before:     # the crossing orders cannot trade (minimum quantities)
                        stuck = True
                    changed = True
            if not changed:
                return
        raise RuntimeError("settle did not converge")

    # -- auctions --------------------------------------------------------------------------------------------------
    def _auction_orders(self, st: _Inst, cross_type: str) -> list[EOrder]:
        orders = [o for side in (1, -1) for p in st.book.prices(side) for o in st.book.level_orders(side, p)
                  if o.display not in "MP"]
        orders += st.mkt
        if cross_type == "C":
            orders += st.close
        return orders

    def _uncross_calc(self, st: _Inst, cross_type: str):
        orders = self._auction_orders(st, cross_type)
        ao = [AuctionOrder(str(i), o.side, o.remaining, o.limit if o.limit else None, o.seq)
              for i, o in enumerate(orders)]
        ref = st.ref_price or st.last
        return orders, uncross(ao, ref)

    def _uncross(self, st: _Inst, cross_type: str) -> None:
        orders, u = self._uncross_calc(st, cross_type)
        self._touched.add(st.locate)
        if u.volume > 0:
            self.next_match += 1
            m, p = self.next_match, u.price
            for oid, q in u.fills:
                o = orders[int(oid)]
                if o.where == "book":
                    shown = min(q, o.qty)
                    if o.visible:
                        self._feed.append(F["C"](st.locate, 0, self.ts, o.ref, shown, m, "N", p))
                    st.book.reduce(o.ref, shown)
                    o.reserve -= q - shown
                    if o.qty == 0 and o.reserve > 0:
                        s2 = min(o.display_qty, o.reserve)
                        o.reserve -= s2
                        o.qty, o.ref, o.seq, o.top = s2, self._new_ref(), self._next_seq(), False
                        st.book.add(o)
                        self._feed.append(F["A"](st.locate, 0, self.ts, o.ref, "B" if o.side == 1 else "S", s2,
                                                 st.symbol, o.price))
                    elif o.qty == 0:
                        o.where = ""
                else:
                    o.qty -= q
                    if o.qty == 0:
                        (st.mkt if o.where == "mkt" else st.close).remove(o)
                        o.where = ""
                self._rep_to(o.session, OUT["E"](self.ts, o.cl, q, p, m, "C", fee(self.cfg, "C", p, q), o.remaining))
                if o.remaining == 0:
                    self._done(o)
                self.trades.append((m, st.locate, p, q, o.session, 0, o.side, "C", o.cl))
            self._feed.append(F["Q"](st.locate, 0, self.ts, u.volume, st.symbol, p, m, cross_type))
            st.last, st.ref_price = p, p
        leftovers = [o for o in list(st.mkt)]
        if cross_type == "O":
            leftovers += [o for side in (1, -1) for px in st.book.prices(side) for o in st.book.level_orders(side, px)
                          if o.tif == "O"]
        if cross_type == "C":
            leftovers += list(st.close)
        for o in sorted(leftovers, key=lambda x: x.seq):
            if o.where:
                self._cancel(o, "I" if o.where == "mkt" else "E")

    # -- control ---------------------------------------------------------------------------------------------------
    def _scope(self, locate: int) -> list[_Inst]:
        return [self.inst[k] for k in sorted(self.inst)] if locate == 0 else [self.inst[locate]]

    def _ctl_L(self, m):
        s = self.sessions.get(m.session)
        if s is None:
            self.sessions[m.session] = _Sess(m.firm, m.cod == "Y", self.burst)
        else:
            s.logged, s.cod = True, m.cod == "Y"

    def _ctl_D(self, m):
        s = self.sessions.get(m.session)
        if s is None:
            return
        s.logged = False
        if s.cod:
            for o in sorted(s.live.values(), key=lambda x: x.seq):
                self._cancel(o, "D")

    def _ctl_P(self, m):
        for st in self._scope(m.locate):
            old, st.phase = st.phase, m.phase
            self._feed.append(F["H"](st.locate, 0, self.ts, st.symbol, STATE[m.phase], " ", m.reason))
            self._touched.add(st.locate)
            if old in CALL_PHASES and m.phase in "TC" and old != m.phase:
                self._uncross(st, CROSS_OF_CALL[old])
            elif old == "T" and m.phase == "C":
                self._uncross(st, "C")

    def _ctl_X(self, m):
        for st in self._scope(m.locate):
            self._uncross(st, m.cross_type)

    def _ctl_I(self, m):
        for st in self._scope(m.locate):
            _, u = self._uncross_calc(st, m.cross_type)
            if u.volume == 0:
                d, p = "O", 0
            else:
                d, p = ("B" if u.surplus > 0 else "S" if u.surplus < 0 else "N"), u.price
            self._feed.append(F["I"](st.locate, 0, self.ts, u.volume, abs(u.surplus), d, st.symbol, p, p,
                                     st.ref_price, m.cross_type, " "))

    def _ctl_R(self, m):
        st = self.inst[m.locate]
        st.ref_price, st.band = m.ref_price, (m.band_lo, m.band_hi)

    def _ctl_N(self, m):
        """A reference quote for midpoint pegs (a dark venue's view of the lit market); 0 on either side clears it."""
        st = self.inst[m.locate]
        st.ref_quote = (m.bid, m.ask) if m.bid > 0 and m.ask > 0 else None
        self._touched.add(m.locate)

    def _ctl_E(self, m):
        orders = [o for s in self.sessions.values() for o in s.live.values()
                  if (m.locate == 0 or o.locate == m.locate) and (m.tif == "A" or o.tif != "G")]
        for o in sorted(orders, key=lambda x: x.seq):
            self._cancel(o, "E")

    def _ctl_F(self, m):
        for st in self._scope(m.locate):
            st.frozen = m.freeze == "Y"

    def _ctl_S(self, m):
        self._feed.append(F["S"](0, 0, self.ts, m.event))
        if m.event == "O":
            for st in self._scope(0):
                self._feed.append(F["R"](st.locate, 0, self.ts, st.symbol, st.tick, st.lot, st.matching))
        for sid in sorted(self.sessions):
            if self.sessions[sid].logged:
                self._rep_to(sid, OUT["S"](self.ts, m.event))


def _msg_cl(m) -> int:
    name = type(m).__name__[-1]
    if name in "OUX":
        return m.cl_ord_id
    if name == "Q":
        return m.quote_id * 2
    return 0
