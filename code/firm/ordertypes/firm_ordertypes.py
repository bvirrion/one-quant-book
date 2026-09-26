"""firm.ordertypes -- the order-type layer of the exchange simulator (build of One Quant Book 10, chapter 2).

An order type is a contract about what the matching engine does with an order. This module holds the rules the
engine (firm.exchsim) applies before and around matching, one function per rule, so that chapter 2 can test each
rule alone and the C++20 and Rust engines can be checked against it scenario by scenario:

  price condition   limit (price > 0) or market (price 0); a stop order waits for a trade at or through its
                    stop price, then enters as a market (price 0) or stop-limit (price > 0) order
  time in force     D day, G good till cancelled, I immediate or cancel, F fill or kill, O at the open, C at the close
  display           Y visible, N hidden, M midpoint peg (hidden, priced at the mid of the displayed quotes, capped by
                    its limit), P primary peg (visible, joins the best displayed price of its own side among the
                    orders that are not pegged, capped by its limit); display_qty > 0 makes a visible order an
                    iceberg: that much is shown, the rest is reserve, refreshed at the back of the queue
  restrictions      post-only (rejected if it would execute on arrival), min_qty (only for IOC orders and midpoint
                    pegs: execute only against at least that much), self-trade prevention by (firm, group)

API (stable):
    EOrder                                     the engine's order (a firm_lob.Order with the fields below)
    validate(o, inst, phase, frozen, band) -> reject reason or None   reasons as in the protocol (J message)
    CALL_PHASES, TRADING                       phases in which orders accumulate / match
    slice_for_display(o)                       (shown, reserve) for a visible order's remaining quantity
    peg_target(o, book, pegged_refs, ref=None) the price a pegged order should rest at now, or None (inactive)
    stp_conflict(a, b) / stp_actions(mode)     do two orders collide; what happens: (cancel resting,
                                               cancel incoming, decrement both)
    stop_triggered(o, last_trade)              has a stop order's trigger been reached
    marketable(side, limit, price)             can an order of `side` and `limit` (None = market) trade at price
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lob"))
from firm_lob import LimitOrderBook, Order  # noqa: E402

CALL_PHASES = frozenset("OKUB")          # opening call, closing call, paused (reopening), batch call
TRADING = "T"
MAX_QTY = 1_000_000_000


class EOrder(Order):
    """A resting or waiting order in the engine. `qty` is what can execute at its level now (an iceberg's shown
    slice), `reserve` the iceberg's hidden rest, `limit` the price the owner gave (0 = market), `price` where it
    rests now (a peg moves), `where` which container holds it: book, stop, mkt (market order in a call), close
    (at-the-close order waiting for the closing cross), peg (inactive peg), or '' once done."""

    __slots__ = ("cl", "session", "firm", "locate", "tif", "display", "post_only", "display_qty", "reserve",
                 "min_qty", "stp_group", "stp_mode", "stop_price", "limit", "where", "top")

    def __init__(self, ref, side, price, qty, *, cl, session, firm, locate, tif="D", display="Y", post_only=False,
                 display_qty=0, reserve=0, min_qty=0, stp_group=0, stp_mode="N", stop_price=0, limit=0, seq=0):
        super().__init__(ref, side, price, qty, visible=display in "YP", seq=seq, owner=session)
        self.cl, self.session, self.firm, self.locate = cl, session, firm, locate
        self.tif, self.display, self.post_only = tif, display, post_only
        self.display_qty, self.reserve, self.min_qty = display_qty, reserve, min_qty
        self.stp_group, self.stp_mode, self.stop_price, self.limit = stp_group, stp_mode, stop_price, limit
        self.where, self.top = "", False

    @property
    def remaining(self) -> int:
        return self.qty + self.reserve


def marketable(side: int, limit: int, price: int) -> bool:
    """limit 0 is a market order."""
    if limit == 0:
        return True
    return price <= limit if side == 1 else price >= limit


def validate(msg, inst, phase: str, frozen: bool, band: tuple[int, int]) -> str | None:
    """First failing rule for an Enter message (namedtuple In_O), as the J reason; None if acceptable.
    `inst` has .tick; band is (lo, hi), 0 = none. Duplicates and post-only are checked by the engine."""
    if phase in "CH":
        return "H"
    if msg.qty <= 0 or msg.qty > MAX_QTY or msg.display_qty > msg.qty:
        return "Q"
    if msg.side not in "BS" or msg.tif not in "DGIFOC" or msg.display not in "YNMP" or msg.stp_mode not in "NOWBD":
        return "Q"
    if msg.min_qty and not (msg.tif == "I" or msg.display == "M"):
        return "Q"
    if msg.display_qty and msg.display != "Y":
        return "Q"
    if msg.price % inst.tick or msg.stop_price % inst.tick:
        return "X"
    if msg.tif == "O" and phase != "O":
        return "H"
    if msg.tif == "C" and (frozen or phase not in "TKO"):
        return "C" if frozen else "H"
    if msg.price and band[1] and not band[0] <= msg.price <= band[1]:
        return "B"
    return None


def slice_for_display(o: EOrder, remaining: int) -> tuple[int, int]:
    if o.visible and o.display_qty:
        shown = min(o.display_qty, remaining)
        return shown, remaining - shown
    return remaining, 0


def peg_target(o: EOrder, book: LimitOrderBook, pegged: set[int], ref: tuple[int, int] | None = None) -> int | None:
    """Midpoint peg: the mid of the reference quote `ref` (bid, ask) when given, else of the best displayed bid and
    ask (None if a side is empty), capped by the limit. Primary peg: the best displayed price on its own side among
    unpegged orders (None if there is none), capped."""
    if o.display == "M":
        b, a = ref if ref is not None else (book.best_visible(1), book.best_visible(-1))
        if b is None or a is None:
            return None
        p = (b + a) // 2
    else:
        p = None
        for px in book.prices(o.side):
            if any(x.visible and x.ref not in pegged for x in book.level_orders(o.side, px)):
                p = px
                break
        if p is None:
            return None
    if o.limit:
        p = min(p, o.limit) if o.side == 1 else max(p, o.limit)
    return p


def stp_conflict(a: EOrder, b: EOrder) -> bool:
    return a.stp_group != 0 and a.stp_group == b.stp_group and a.firm == b.firm


def stp_actions(mode: str) -> tuple[bool, bool, bool]:
    """(cancel the resting order, cancel the incoming order, decrement both) for the incoming order's mode."""
    return {"O": (True, False, False), "W": (False, True, False), "B": (True, True, False),
            "D": (False, False, True)}.get(mode, (False, False, False))


def stop_triggered(o: EOrder, last_trade: int) -> bool:
    if last_trade <= 0:
        return False
    return last_trade >= o.stop_price if o.side == 1 else last_trade <= o.stop_price
