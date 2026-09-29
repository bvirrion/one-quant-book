"""firm.tradecap -- trade capture, a canonical trade model, allocations and the lifecycle as events (Book 15, ch. 21).

A trade is data: a header (unique transaction identifier, trade identifier, parties by legal entity identifier, book,
trade and settlement dates) and an economic part (the instrument as Book 5's pricing library serialises it, a quantity
and a price). A trade is never edited: it is the result of its events -- new, amend, novate, partially terminate,
exercise, cancel, allocate -- applied in order, each with its time, so that any version as of any time can be rebuilt
and every system that follows the events holds the same trade. Capture adapters turn exchange execution reports and
OTC tickets into new-trade events; a block fill is allocated to funds at its average price with a stated rule for the
shares that do not divide evenly; a booking model maps an instrument type and a desk to a book.

API (stable):
    uti(lei, n) -> str                              LEI of the generating entity + a unique value, <= 52 chars, A-Z0-9
    validate(trade) -> [str]                        the canonical model's rules
    Event(ts, kind, trade_id, data)                 kinds: new, amend, novate, terminate, exercise, cancel, allocate
    TradeStore().apply(event) ; .as_of(trade_id, ts=None) -> dict | None ; .versions(trade_id) -> [(ts, version)]
    from_execution(report, lei, book, ...) -> Event ; from_ticket(ticket) -> Event
    allocate(fills [(qty, price)], weights {fund: w}, rule, lot=1) -> {fund: (qty, avg price)}, residual
        rules: 'largest-remainder', 'floor-then-largest', 'round-each'
    BookingModel(rules {(instrument type, desk): book path}).book(instrument, desk)
"""
from __future__ import annotations

import copy
import math
import re
from dataclasses import dataclass, field

LEI = re.compile(r"^[A-Z0-9]{18}[0-9]{2}$")
UTI = re.compile(r"^[A-Z0-9]{1,52}$")
KINDS = ("new", "amend", "novate", "terminate", "exercise", "cancel", "allocate")
REQUIRED = ("uti", "trade_id", "buyer", "seller", "book", "trade_date", "settle_date", "instrument", "quantity",
            "price")


def uti(lei: str, n: int) -> str:
    """CPMI-IOSCO structure: the generating entity's LEI followed by a value unique for that entity."""
    if not LEI.match(lei):
        raise ValueError(f"not an LEI: {lei}")
    return f"{lei}{n:032d}"[:52]


def validate(t: dict) -> list[str]:
    errs = [f"missing {k}" for k in REQUIRED if k not in t]
    if errs:
        return errs
    if not UTI.match(t["uti"]):
        errs.append("UTI must be 1-52 characters A-Z, 0-9")
    for side in ("buyer", "seller"):
        if not LEI.match(t[side]):
            errs.append(f"{side} is not an LEI")
    if t["buyer"] == t["seller"]:
        errs.append("buyer and seller are the same entity")
    if t["settle_date"] < t["trade_date"]:
        errs.append("settlement before trade date")
    if t["quantity"] <= 0:
        errs.append("quantity must be positive")
    if "type" not in t["instrument"]:
        errs.append("instrument has no type")
    return errs


@dataclass(frozen=True)
class Event:
    ts: float
    kind: str
    trade_id: str
    data: dict = field(default_factory=dict)


class TradeStore:
    """Event-sourced trades: the log is the truth, states are replays."""

    def __init__(self):
        self.log: list[Event] = []

    def apply(self, e: Event) -> None:
        if e.kind not in KINDS:
            raise ValueError(f"unknown event {e.kind}")
        if e.kind != "new" and self.as_of(e.trade_id, e.ts) is None:
            raise ValueError(f"{e.kind} on a trade that does not exist: {e.trade_id}")
        self.log.append(e)

    def as_of(self, trade_id: str, ts: float | None = None) -> dict | None:
        state = None
        mine = sorted((x for x in self.log if x.trade_id == trade_id), key=lambda x: x.ts)
        for e in mine:
            if ts is not None and e.ts > ts:
                break
            state = _step(state, e)
        return state

    def versions(self, trade_id: str) -> list[tuple]:
        out, state = [], None
        mine = sorted((x for x in self.log if x.trade_id == trade_id), key=lambda x: x.ts)
        for e in mine:
            state = _step(state, e)
            out.append((e.ts, state["version"]))
        return out


def _step(state, e: Event) -> dict:
    if e.kind == "new":
        s = copy.deepcopy(e.data)
        s.update(version=1, status="live")
        return s
    s = copy.deepcopy(state)
    s["version"] += 1
    if e.kind == "amend":
        s.update(e.data)
    elif e.kind == "novate":                         # a party steps out, another steps in
        s[e.data["side"]] = e.data["new"]
    elif e.kind == "terminate":                  # partial termination: the quantity falls
        s["quantity"] -= e.data["quantity"]
        if s["quantity"] <= 0:
            s["status"] = "terminated"
    elif e.kind == "exercise":
        s["status"] = "exercised"
        s["instrument"] = e.data["into"]
    elif e.kind == "cancel":
        s["status"] = "cancelled"
    elif e.kind == "allocate":
        s["status"] = "allocated"
        s["allocations"] = e.data["allocations"]
    return s


# ------------------------------------------------------------ capture adapters
def from_execution(report: dict, lei: str, counterparty: str, book: str, n: int, instrument: dict) -> Event:
    """An exchange execution report (quantity, price, time, side) as a new trade against the venue's CCP."""
    buy = report["side"] == 1
    trade = {"uti": uti(lei, n), "trade_id": f"X{n}", "buyer": lei if buy else counterparty,
             "seller": counterparty if buy else lei, "book": book, "trade_date": report["date"],
             "settle_date": report["date"] + 1, "instrument": instrument, "quantity": report["qty"],
             "price": report["price"], "source": "exchange"}
    return Event(report["ts"], "new", trade["trade_id"], trade)


def from_ticket(ticket: dict) -> Event:
    trade = dict(ticket, source="ticket")
    return Event(ticket["ts"], "new", ticket["trade_id"], trade)


# ------------------------------------------------------------ allocation
def allocate(fills, weights: dict, rule: str = "largest-remainder", lot: int = 1):
    """Split a block among funds at its average price, in whole lots; the rule decides where
    the lots that do not divide go. Returns the allocations and the residual."""
    total = sum(q for q, _ in fills)
    avg = sum(q * p for q, p in fills) / total
    lots = total // lot
    wsum = sum(weights.values())
    exact = {f: lots * w / wsum for f, w in weights.items()}
    if rule == "round-each":
        n = {f: int(math.floor(x + 0.5)) for f, x in exact.items()}
    else:
        n = {f: int(math.floor(x)) for f, x in exact.items()}
        left = lots - sum(n.values())
        if rule == "largest-remainder":
            order = sorted(exact, key=lambda f: (-(exact[f] - n[f]), f))
        elif rule == "floor-then-largest":
            order = sorted(exact, key=lambda f: (-weights[f], f))
        else:
            raise ValueError(rule)
        for f in order[:left]:
            n[f] += 1
    alloc = {f: (k * lot, avg) for f, k in n.items()}
    return alloc, total - sum(q for q, _ in alloc.values())


@dataclass
class BookingModel:
    rules: dict                                      # (instrument type, desk) -> book path

    def book(self, instrument: dict, desk: str) -> str:
        key = (instrument["type"], desk)
        if key not in self.rules:
            raise KeyError(f"no booking rule for {key}")
        return self.rules[key]
