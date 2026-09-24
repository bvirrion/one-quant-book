"""firm.fees -- per-investor fund fee engine (build of Chapter 3, One Quant Book 1)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class FeeTerms:
    mgmt: float = 0.02               # annual rate, charged pro rata on opening value
    perf: float = 0.20               # share of gains above the (hurdled) high-water mark
    hurdle: float = 0.0              # annual rate by which the mark grows before the test
    periods_per_year: int = 1


@dataclass(frozen=True)
class InvestorState:
    nav: float = 1.0
    high_water: float = 1.0


def accrue(terms: FeeTerms, state: InvestorState, gross_return: float):
    """One period. Returns (new_state, management_fee, performance_fee)."""
    n = terms.periods_per_year
    mgmt = terms.mgmt / n * state.nav
    before_perf = state.nav * (1.0 + gross_return) - mgmt
    mark = state.high_water * (1.0 + terms.hurdle / n)
    perf = max(0.0, terms.perf * (before_perf - mark))
    nav = before_perf - perf
    return InvestorState(nav, max(mark if terms.hurdle else state.high_water, nav)), max(0.0, mgmt), perf
