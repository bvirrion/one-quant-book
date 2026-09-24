"""firm.marketrules -- dated market rules and order validation (build of Chapter 12)."""
import csv
import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class MarketRules:
    market: str
    valid_from: dt.date
    lot: int
    tick: int                 # single tick in price units (a real table is a stretch goal)
    limit_up: float           # fraction of the reference price; 0 = no limit
    limit_down: float
    same_day_sell: bool
    short_selling: bool
    settlement_days: int
    tax_buy: float
    tax_sell: float


@dataclass(frozen=True)
class Order:
    side: int                 # +1 buy, -1 sell
    quantity: int
    price: int


class RuleBook:
    def __init__(self, rules: list[MarketRules]) -> None:
        self._rules = sorted(rules, key=lambda r: (r.market, r.valid_from))

    @classmethod
    def load(cls, path: str) -> "RuleBook":
        out = []
        with open(path, newline="", encoding="utf8") as f:
            for r in csv.DictReader(f):
                out.append(MarketRules(r["market"], dt.date.fromisoformat(r["valid_from"]), int(r["lot"]),
                                       int(r["tick"]), float(r["limit_up"]), float(r["limit_down"]),
                                       r["same_day_sell"] == "1", r["short_selling"] == "1",
                                       int(r["settlement_days"]), float(r["tax_buy"]), float(r["tax_sell"])))
        return cls(out)

    def rules(self, market: str, date: dt.date) -> MarketRules:
        found = [r for r in self._rules if r.market == market and r.valid_from <= date]
        if not found:
            raise KeyError(f"no rules for {market} on {date}")
        return found[-1]

    def limit_band(self, market: str, date: dt.date, reference: int) -> tuple[int, int]:
        """Lowest and highest allowed prices, rounded inward to the tick."""
        r = self.rules(market, date)
        if r.limit_up == 0 and r.limit_down == 0:
            return (r.tick, 10**15)
        hi = int(reference * (1 + r.limit_up)) // r.tick * r.tick
        lo = -(-int(reference * (1 - r.limit_down) + 0.999999) // r.tick) * r.tick
        return (lo, hi)

    def validate(self, market: str, date: dt.date, order: Order, reference: int, opening_position: int) -> list[str]:
        r, bad = self.rules(market, date), []
        if order.quantity <= 0 or order.quantity % r.lot:
            bad.append("quantity is not a multiple of the lot")
        if order.price % r.tick:
            bad.append("price is not a multiple of the tick")
        lo, hi = self.limit_band(market, date, reference)
        if not lo <= order.price <= hi:
            bad.append("price outside the daily limit")
        if order.side < 0:
            if order.quantity > max(opening_position, 0):
                if not r.same_day_sell and opening_position >= 0:
                    bad.append("sale exceeds the position held at the start of the day")
                elif not r.short_selling:
                    bad.append("short selling is not allowed")
        return bad

    def tax(self, market: str, date: dt.date, side: int, value: float) -> float:
        r = self.rules(market, date)
        return value * (r.tax_buy if side > 0 else r.tax_sell)
