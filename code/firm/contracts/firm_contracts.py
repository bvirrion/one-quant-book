"""Contract master (build of Book 1, Chapter 18): reference data for futures.

Everything downstream (P&L, margin, order entry) works in integer ticks; this module is the only
place where a price becomes ticks and ticks become money.
"""
import csv
import datetime as dt
from dataclasses import dataclass
from fractions import Fraction

MONTH_CODES = "FGHJKMNQUVXZ"                       # January .. December


@dataclass(frozen=True)
class ContractSpec:
    root: str
    name: str
    exchange: str
    currency: str
    multiplier: Fraction                            # currency units per one full price point
    tick_size: Fraction
    quote_style: str                                # 'decimal' or 'thirty_seconds'
    months: str
    settlement: str
    last_trade_rule: str

    @property
    def tick_value(self) -> Fraction:
        return self.multiplier * self.tick_size

    def to_ticks(self, price: Fraction | str) -> int:
        q = Fraction(price) / self.tick_size
        if q.denominator != 1:
            raise ValueError(f"{price} is not on the {self.root} tick grid")
        return int(q)

    def from_ticks(self, ticks: int) -> Fraction:
        return ticks * self.tick_size

    def notional(self, price: Fraction | str) -> Fraction:
        return Fraction(price) * self.multiplier


@dataclass(frozen=True)
class Instrument:
    spec: ContractSpec
    year: int
    month: int

    @property
    def symbol(self) -> str:
        return f"{self.spec.root}{MONTH_CODES[self.month - 1]}{self.year % 10}"


def third_friday(year: int, month: int) -> dt.date:
    first = dt.date(year, month, 1)
    return first + dt.timedelta(days=(4 - first.weekday()) % 7 + 14)


def parse_thirty_seconds(text: str) -> Fraction:
    """'112-165' -> 112 + 16.5/32. The third digit after the dash counts eighths of a 32nd:
    0, 2 (a quarter), 5 (a half), 7 (three quarters)."""
    whole, frac = text.split("-")
    eighths = {"": 0, "0": 0, "2": 2, "5": 4, "7": 6}
    if len(frac) not in (2, 3) or frac[2:] not in eighths:
        raise ValueError(f"cannot read {text!r}")
    return int(whole) + (Fraction(int(frac[:2])) + Fraction(eighths[frac[2:]], 8)) / 32


class ContractMaster:
    def __init__(self, specs: list[ContractSpec]) -> None:
        self._specs: dict[str, ContractSpec] = {}
        for s in specs:
            if s.root in self._specs:
                raise ValueError(f"duplicate root {s.root}")
            if s.multiplier <= 0 or s.tick_size <= 0 or not set(s.months) <= set(MONTH_CODES):
                raise ValueError(f"bad specification for {s.root}")
            self._specs[s.root] = s

    @classmethod
    def from_csv(cls, path: str) -> "ContractMaster":
        with open(path, newline="") as f:
            return cls([ContractSpec(r["root"], r["name"], r["exchange"], r["currency"], Fraction(r["multiplier"]),
                                     Fraction(r["tick_size"]), r["quote_style"], r["months"], r["settlement"],
                                     r["last_trade_rule"]) for r in csv.DictReader(f)])

    def spec(self, root: str) -> ContractSpec:
        return self._specs[root]

    def parse(self, symbol: str, today: dt.date) -> Instrument:
        """'ESZ6' -> December of the first year ending in 6 that is not in the past."""
        root, code, digit = symbol[:-2], symbol[-2], symbol[-1]
        spec = self._specs[root]
        if code not in spec.months or not digit.isdigit():
            raise ValueError(f"{symbol}: month {code!r} is not listed for {root}")
        month = MONTH_CODES.index(code) + 1
        year = today.year - today.year % 10 + int(digit)
        if (year, month) < (today.year, today.month):
            year += 10
        return Instrument(spec, year, month)

    def expiry(self, inst: Instrument) -> dt.date:
        if inst.spec.last_trade_rule != "third_friday":
            raise NotImplementedError(f"{inst.spec.root}: load the exchange calendar")
        return third_friday(inst.year, inst.month)
