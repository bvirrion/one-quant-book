"""firm.financing -- nightly financing accrual (build of Chapter 6, One Quant Book 1)."""
import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class FinancingTerms:
    debit_spread: float      # added to the rate on debit balances
    credit_spread: float     # subtracted from the rate on short proceeds
    day_count: int = 360


@dataclass(frozen=True)
class Accrual:
    debit_interest: float    # negative = cost
    short_interest: float    # positive = income
    borrow_fees: float       # negative = cost

    @property
    def total(self) -> float:
        return self.debit_interest + self.short_interest + self.borrow_fees


def days_accrued(date: dt.date) -> int:
    """Calendar days until the next business day: Friday accrues three."""
    return 3 if date.weekday() == 4 else 1


def accrue(date: dt.date, positions: dict[str, float], prices: dict[str, float], equity: float,
           rate: float, terms: FinancingTerms, borrow_fees: dict[str, float]) -> Accrual:
    """positions: settled quantities (signed); prices: previous close."""
    long_value = sum(q * prices[s] for s, q in positions.items() if q > 0)
    fees = 0.0
    short_value = 0.0
    for s, q in positions.items():
        if q < 0:
            if s not in borrow_fees:
                raise KeyError(f"no borrow fee for short position {s}")
            v = -q * prices[s]
            short_value += v
            fees += v * borrow_fees[s]
    frac = days_accrued(date) / terms.day_count
    debit = max(0.0, long_value - equity)
    return Accrual(-debit * (rate + terms.debit_spread) * frac,
                   short_value * (rate - terms.credit_spread) * frac, -fees * frac)
