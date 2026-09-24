"""Pre-trade prime-broker limit gate (build of Book 2, Chapter 27): the Python reference and reader.

The production gate is C++20 (cpp/firm_pblimits.hpp) and Rust (rust/src/lib.rs); this module holds
the same logic for analysis, reads the limits file, and replays orders. Each prime broker's notice
gives allowed pairs, a maximum tenor, a net open position (NOP) limit and a settlement limit per
value date. NOP is the sum of the net long dollar values across currencies (equal to the sum of the
shorts, half the gross); the settlement amount of a value date is the sum of the dollar values of the
currencies to be received that day. An order is accepted if it keeps both measures within their
limits, or does not increase one that is already above its limit.
"""
import csv
from dataclasses import dataclass, field


@dataclass
class Limits:
    pb: str
    fee_per_m: float                   # USD per million USD traded
    nop_limit: float                   # USD
    settle_limit: float                # USD per value date
    max_tenor: int                     # days
    pairs: frozenset[str]


@dataclass(frozen=True)
class Order:
    pair: str                          # e.g. "EURUSD": base then quote
    buy: bool                          # buy the base currency
    amount: float                      # in base currency
    rate: float                        # quote per base
    value_day: int                     # days from today


@dataclass
class Book:
    limits: Limits
    net: dict[str, float] = field(default_factory=dict)                      # USD value by currency
    settle: dict[int, dict[str, float]] = field(default_factory=dict)        # day -> currency -> USD

    def nop(self, net: dict[str, float] | None = None) -> float:
        return sum(v for v in (net or self.net).values() if v > 0)

    def settlement(self, day: int, flows: dict[str, float] | None = None) -> float:
        return sum(v for v in (flows if flows is not None else self.settle.get(day, {})).values() if v > 0)


def legs(order: Order, usd_per: dict[str, float]) -> dict[str, float]:
    """USD value of each currency received (+) or paid (-) by the fund."""
    base, quote = order.pair[:3], order.pair[3:]
    b = order.amount * usd_per[base]
    q = order.amount * order.rate * usd_per[quote]
    sign = 1.0 if order.buy else -1.0
    return {base: sign * b, quote: -sign * q}


def check(book: Book, order: Order, usd_per: dict[str, float]) -> str:
    """'ok' or the reason for rejection; the book is not changed."""
    lim = book.limits
    if order.pair not in lim.pairs:
        return "pair"
    if order.value_day > lim.max_tenor:
        return "tenor"
    lg = legs(order, usd_per)
    net = dict(book.net)
    flows = dict(book.settle.get(order.value_day, {}))
    for c, v in lg.items():
        net[c] = net.get(c, 0.0) + v
        flows[c] = flows.get(c, 0.0) + v
    new_nop, old_nop = book.nop(net), book.nop()
    if new_nop > lim.nop_limit and new_nop > old_nop:
        return "nop"
    new_set, old_set = book.settlement(order.value_day, flows), book.settlement(order.value_day)
    if new_set > lim.settle_limit and new_set > old_set:
        return "settlement"
    return "ok"


def apply(book: Book, order: Order, usd_per: dict[str, float]) -> None:
    day = book.settle.setdefault(order.value_day, {})
    for c, v in legs(order, usd_per).items():
        book.net[c] = book.net.get(c, 0.0) + v
        day[c] = day.get(c, 0.0) + v


def route(books: list[Book], order: Order, usd_per: dict[str, float]) -> tuple[str | None, list[str]]:
    """Give the order up to the cheapest prime broker that accepts it; return it and every reason."""
    reasons = []
    for b in sorted(books, key=lambda x: x.limits.fee_per_m):
        r = check(b, order, usd_per)
        reasons.append(f"{b.limits.pb}:{r}")
        if r == "ok":
            apply(b, order, usd_per)
            return b.limits.pb, reasons
    return None, reasons


def read_limits(path: str) -> list[Limits]:
    """Read the limits file shared with the C++ and Rust gates: pb,fee_per_m,nop_limit,settle_limit,
    max_tenor,pairs (pairs separated by ';')."""
    with open(path) as f:
        return [Limits(r["pb"], float(r["fee_per_m"]), float(r["nop_limit"]), float(r["settle_limit"]),
                       int(r["max_tenor"]), frozenset(r["pairs"].split(";"))) for r in csv.DictReader(f)]
