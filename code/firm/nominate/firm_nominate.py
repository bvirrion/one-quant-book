"""Schedule nominations and physical credit checks (build of Book 3, Chapter 13).

A balancing group nominates, for each market time unit (MTU), its own forecast injections and
withdrawals and its trades with other groups (by their codes). The nomination is balanced when
injections plus purchases equal withdrawals plus sales. Energy in MWh per MTU; money in euros.
"""
import datetime as dt
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Nomination:
    group: str
    injections: dict[int, float] = field(default_factory=lambda: defaultdict(float))
    withdrawals: dict[int, float] = field(default_factory=lambda: defaultdict(float))
    trades: dict[tuple[int, str], float] = field(default_factory=lambda: defaultdict(float))   # + bought from

    def add_trade(self, mtu: int, counterparty: str, qty: float) -> None:
        if counterparty == self.group:
            raise ValueError("a group cannot trade with itself")
        self.trades[(mtu, counterparty)] += qty

    def net(self, mtu: int) -> float:
        """Injections + purchases - withdrawals - sales: zero for a balanced schedule."""
        traded = sum(q for (m, _), q in self.trades.items() if m == mtu)
        return self.injections[mtu] + traded - self.withdrawals[mtu]

    def unbalanced(self, mtus: range, tol: float = 1e-6) -> dict[int, float]:
        return {m: self.net(m) for m in mtus if abs(self.net(m)) > tol}


def counterparty_mismatches(a: Nomination, b: Nomination, mtus: range) -> dict[int, float]:
    """MTUs in which what A says it trades with B is not the opposite of what B says it trades with A."""
    out = {}
    for m in mtus:
        diff = a.trades.get((m, b.group), 0.0) + b.trades.get((m, a.group), 0.0)
        if abs(diff) > 1e-6:
            out[m] = diff
    return out


def in_time(submitted: dt.datetime, delivery_day: dt.date, deadline: dt.time, days_before: int = 1) -> bool:
    """Whether a nomination was submitted before its deadline on the day(s) before delivery."""
    cutoff = dt.datetime.combine(delivery_day - dt.timedelta(days=days_before), deadline)
    return submitted <= cutoff


def uncovered_exposure(unpaid_deliveries: float, forward_mtm: float, letter_of_credit: float) -> float:
    """Credit exposure to a physical counterparty not covered by its letter of credit: energy delivered
    and not yet paid, plus the replacement value of future deliveries if positive to us."""
    return max(unpaid_deliveries + max(forward_mtm, 0.0) - letter_of_credit, 0.0)


def carry_cost(collateral: float, rate: float, years: float = 1.0) -> float:
    """Cost of funding posted collateral (simple interest)."""
    return collateral * rate * years
