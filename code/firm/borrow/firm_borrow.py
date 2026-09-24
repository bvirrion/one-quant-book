"""Borrow-cost model (build of Book 1, Chapter 16): locates, utilisation-driven fees, recalls.

Feeds `firm_financing.accrue`, whose `borrow_fees` argument is a dict symbol -> annual fee.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FeeCurve:
    gc: float = 0.003                 # general-collateral fee, annual
    kink: float = 0.75                # utilisation above which the security goes special
    max_fee: float = 0.80

    def fee(self, utilisation: float) -> float:
        if utilisation <= self.kink:
            return self.gc
        x = (min(utilisation, 1.0) - self.kink) / (1.0 - self.kink)
        return self.gc + (self.max_fee - self.gc) * x * x


@dataclass
class Line:
    lendable: int                     # shares the lenders make available
    on_loan_others: int               # borrowed by the rest of the market
    ours: int = 0                     # borrowed by the firm


@dataclass
class BorrowBook:
    curve: FeeCurve = field(default_factory=FeeCurve)
    lines: dict[str, Line] = field(default_factory=dict)

    def utilisation(self, sym: str) -> float:
        ln = self.lines[sym]
        return (ln.on_loan_others + ln.ours) / ln.lendable if ln.lendable else 1.0

    def available(self, sym: str) -> int:
        ln = self.lines[sym]
        return max(0, ln.lendable - ln.on_loan_others - ln.ours)

    def locate(self, sym: str, qty: int) -> int:
        """Shares that can be borrowed now (0 for an unknown symbol): the answer to a locate request."""
        return min(qty, self.available(sym)) if sym in self.lines else 0

    def borrow(self, sym: str, qty: int) -> int:
        got = self.locate(sym, qty)
        if got:
            self.lines[sym].ours += got
        return got

    def give_back(self, sym: str, qty: int) -> None:
        ln = self.lines[sym]
        ln.ours -= min(qty, ln.ours)

    def recall(self, sym: str, qty: int) -> int:
        """A lender withdraws `qty` shares. Returns the shares the firm must buy in: the part of its
        borrow that can no longer be sourced from what remains lendable."""
        ln = self.lines[sym]
        ln.lendable = max(0, ln.lendable - qty)
        excess = ln.on_loan_others + ln.ours - ln.lendable
        if excess <= 0:
            return 0
        share = min(ln.ours, -(-excess * ln.ours // (ln.on_loan_others + ln.ours)))   # pro rata, rounded up
        ln.ours -= share
        ln.on_loan_others -= excess - share
        return share

    def borrow_fees(self) -> dict[str, float]:
        return {s: self.curve.fee(self.utilisation(s)) for s in self.lines}
