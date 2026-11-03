import csv
from collections.abc import Iterable, Iterator
from fractions import Fraction
from typing import NamedTuple


class Trade(NamedTuple):
    symbol: str
    price: Fraction
    qty: int


def parse(rows: Iterable[dict], errors: list) -> Iterator[Trade]:
    for n, row in enumerate(rows, 1):
        try:
            yield Trade(row["symbol"], Fraction(row["price"]), int(row["qty"]))
        except (KeyError, ValueError, TypeError, ZeroDivisionError) as e:
            errors.append((n, repr(e)))


def vwaps(trades: Iterable[Trade]) -> dict:
    """A pure function: same trades in, same numbers out, and no hidden state."""
    totals = {}
    for t in trades:
        notional, qty = totals.get(t.symbol, (Fraction(0), 0))
        totals[t.symbol] = (notional + t.price * t.qty, qty + t.qty)
    return {s: (n / q if q else None) for s, (n, q) in totals.items()}


def report(path: str) -> tuple[dict, list]:
    errors = []
    with open(path, newline="") as f:
        return vwaps(parse(csv.DictReader(f), errors)), errors
