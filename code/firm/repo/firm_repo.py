"""Repo book (build of Book 2, Chapter 5): repo and reverse repo trades, accrual, margin calls,
specialness and the fails charge. Cash in currency units, rates decimal, actual/360.

A repo is seen from the side that sells the collateral and borrows cash (it pays the repo rate);
a reverse repo from the side that lends cash and receives collateral.
"""
import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class RepoTrade:
    side: str                  # "repo" (borrow cash) or "reverse" (lend cash)
    collateral: str
    face: float
    dirty_price: float         # per 100, at the start
    haircut: float             # fraction of collateral value withheld (0.02 = 2%)
    rate: float
    start: dt.date
    end: dt.date

    @property
    def cash(self) -> float:
        """Cash lent against the collateral: its value less the haircut."""
        return self.face * self.dirty_price / 100.0 * (1.0 - self.haircut)

    def interest(self, until: dt.date | None = None) -> float:
        d = (until or self.end) - self.start
        return self.cash * self.rate * d.days / 360.0

    def repurchase_price(self) -> float:
        return self.cash + self.interest()

    def sign(self) -> int:
        """+1 if this side pays interest (repo), -1 if it earns it (reverse repo)."""
        return 1 if self.side == "repo" else -1


def margin_call(trade: RepoTrade, new_dirty_price: float, accrued_to: dt.date) -> float:
    """Collateral (in cash value) the cash borrower must add, positive, or may withdraw, negative,
    to restore the haircut on the cash plus accrued repo interest."""
    owed = trade.cash + trade.interest(accrued_to)
    required = owed / (1.0 - trade.haircut)
    held = trade.face * new_dirty_price / 100.0
    return required - held


def specialness(gc_rate: float, special_rate: float) -> float:
    return gc_rate - special_rate


def value_of_specialness(dirty_price: float, path: list[tuple[int, float]]) -> float:
    """Price points (per 100) that a holder saves by financing at special rates: the sum over
    periods of days x specialness / 360 on the dirty price. path = [(days, specialness), ...]."""
    return dirty_price * sum(days * s for days, s in path) / 360.0


def fails_charge(proceeds: float, reference_rate_pct: float, days: int = 1, base_pct: float = 3.0) -> float:
    """TMPG fails charge: 1/360 x 0.01 x max(base - R, 0) x P per day (base 3 for Treasuries)."""
    return days * proceeds * 0.01 * max(base_pct - reference_rate_pct, 0.0) / 360.0


def special_rate_floor(reference_rate: float, base: float = 0.03) -> float:
    """Lowest special repo rate a short would accept rather than fail: -(base - R)+."""
    return -max(base - reference_rate, 0.0)


def carry(face: float, coupon_pct: float, dirty_price: float, repo_rate: float, days: int, freq: int = 2,
          period_days: int = 182) -> float:
    """Coupon accrued over `days` less repo interest on the dirty price (actual/actual coupon over a
    period of `period_days`, actual/360 repo), in currency, for a long bond financed in repo."""
    coupon = face * coupon_pct / 100.0 / freq * days / period_days
    financing = face * dirty_price / 100.0 * repo_rate * days / 360.0
    return coupon - financing
