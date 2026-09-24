"""A CLO payment waterfall with overcollateralisation and interest-coverage tests (build of Book 2,
Chapter 25).

Quarterly periods. Each quarter a constant annual default rate removes loans; recoveries are
reinvested in new loans at par during the reinvestment period and otherwise repay the notes in order.
Interest from the loans pays the senior fee, then each class of notes in order of seniority; after a
class is paid, its coverage tests are checked, and a failing test diverts the remaining interest to
repay the most senior notes until it is cured. Unpaid interest on deferrable classes is added to their
balance. The equity receives what is left, and at the end the loans are sold at par and the proceeds
repay the notes in order, the rest going to the equity.
"""
from dataclasses import dataclass, field


@dataclass
class Note:
    name: str
    balance: float
    spread: float                      # over the floating rate, a year
    deferrable: bool = True


@dataclass
class Deal:
    notes: list[Note]
    par: float                         # loan portfolio at par
    loan_spread: float
    rate: float                        # floating rate, flat
    fee: float                         # senior fee, a year, on par
    oc: dict[int, float]               # class index -> trigger on par / notes up to that class
    ic: dict[int, float] = field(default_factory=dict)   # class index -> trigger on interest cover
    recovery: float = 0.70
    quarters: int = 20
    reinvest_quarters: int = 20


@dataclass
class Period:
    quarter: int
    par: float
    oc_ratios: dict[int, float]
    diverted: float
    equity: float
    balances: list[float]


def pay_down(notes: list[Note], amount: float) -> float:
    """Repay notes in order of seniority; return what is left over."""
    for n in notes:
        paid = min(n.balance, amount)
        n.balance -= paid
        amount -= paid
    return amount


def run(deal: Deal, cdr: float) -> list[Period]:
    notes = [Note(n.name, n.balance, n.spread, n.deferrable) for n in deal.notes]
    par, out, q_default = deal.par, [], 1.0 - (1.0 - cdr) ** 0.25
    for t in range(1, deal.quarters + 1):
        defaults = par * q_default
        par -= defaults
        interest = par * (deal.rate + deal.loan_spread) / 4
        recoveries = defaults * deal.recovery
        if t <= deal.reinvest_quarters:
            par += recoveries
            principal = 0.0
        else:
            principal = recoveries
        avail = max(interest - deal.fee * deal.par / 4, 0.0)
        cash_after_fee, due_so_far, diverted, ratios = avail, 0.0, 0.0, {}
        for k, n in enumerate(notes):
            due = n.balance * (deal.rate + n.spread) / 4
            due_so_far += due
            paid = min(avail, due)
            avail -= paid
            if n.deferrable:
                n.balance += due - paid
            senior = sum(m.balance for m in notes[:k + 1])
            if k in deal.oc:
                ratios[k] = par / senior if senior > 0 else float("inf")
                if ratios[k] < deal.oc[k]:
                    cure = min(avail, senior - par / deal.oc[k])
                    pay_down(notes, cure)
                    avail -= cure
                    diverted += cure
            if k in deal.ic and due_so_far > 0 and cash_after_fee / due_so_far < deal.ic[k]:
                pay_down(notes, avail)
                diverted += avail
                avail = 0.0
        avail += pay_down(notes, principal)
        if t == deal.quarters:
            avail += pay_down(notes, par)
        out.append(Period(t, par, ratios, diverted, avail, [n.balance for n in notes]))
    return out


def equity_irr(cash: list[float], invested: float) -> float:
    """Annual internal rate of return of quarterly equity cash flows (bisection on the quarterly rate)."""
    def npv(q: float) -> float:
        return -invested + sum(c / (1 + q) ** (t + 1) for t, c in enumerate(cash))
    lo, hi = -0.99, 1.0
    if npv(lo) < 0:
        return -1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if npv(mid) > 0 else (lo, mid)
    return (1 + 0.5 * (lo + hi)) ** 4 - 1


def cutoff_cdr(deal: Deal, lo: float = 0.0, hi: float = 0.5) -> float:
    """Lowest constant default rate at which the equity receives nothing in some quarter before the end."""
    def cut(cdr: float) -> bool:
        return any(p.equity < 1e-9 for p in run(deal, cdr)[:-1])
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (lo, mid) if cut(mid) else (mid, hi)
    return hi
