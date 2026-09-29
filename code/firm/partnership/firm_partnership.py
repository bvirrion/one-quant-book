"""firm.partnership -- the proprietary trading partnership (build of One Quant Book 16, chapter 2).

Three pieces:

* Members' capital accounts. Each year's profit is allocated to members by points; a member draws a share of
  their allocation (the payout) and the rest is retained in their capital account. A departing member's
  capital is repaid in equal instalments over a number of years.
* The capital requirement of an investment firm dealing on its own account, in the shape of the EU's
  investment-firm rules: the highest of a permanent minimum, a quarter of the preceding year's fixed overheads,
  and activity-based K-factors (a coefficient on the daily trading flow plus a charge on net positions).
  All coefficients are inputs; the defaults are labelled illustrative in the chapter.
* The technology treadmill. Competitors' technology stock grows at a rate g; the firm's stock depreciates at d
  and grows by what it spends. Capture per unit traded is proportional to the firm's relative technology to a
  power eta. Holding capture constant needs spending of (g + d) / (1 + g) of the stock every year.

`simulate` runs a firm for n years under a retention ratio: volume is limited by trading capital (margin per
unit of daily volume) and by the market's size; profit after fixed costs, technology spending and variable pay
is split into payout and retention. Amounts in one currency (the chapter uses millions a year). NumPy only.

API (stable):
    Member(name, points, capital); Partnership(members).allocate(profit, payout_ratio) -> dict of draws
        .depart(name, years) ; .pay_departures() -> amount repaid this year ; .total_capital
    own_funds_requirement(fixed_overheads, dtf_cash, dtf_deriv, npr, permanent=0.75, k_dtf_cash=0.001,
                          k_dtf_deriv=0.0001) -> (requirement, which)
    steady_spend_share(g, d) ; capture(rel, c0, eta)
    Params(...), simulate(params, retention) -> dict of arrays ; target_capital(target) -> policy
    discounted_payout(sim, rate, terminal_multiple)
"""
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Member:
    name: str
    points: float
    capital: float = 0.0


@dataclass
class Partnership:
    members: list
    leaving: dict = field(default_factory=dict)   # name -> (instalment, years left)

    @property
    def total_capital(self) -> float:
        return sum(m.capital for m in self.members) + sum(a * n for a, n in self.leaving.values())

    def allocate(self, profit: float, payout_ratio: float) -> dict:
        """Allocate profit by points; each member draws payout_ratio of their share, the rest is retained.
        A loss is allocated by points too and reduces capital (nothing is drawn)."""
        pts = sum(m.points for m in self.members)
        draws = {}
        for m in self.members:
            share = profit * m.points / pts
            d = payout_ratio * share if share > 0 else 0.0
            m.capital += share - d
            draws[m.name] = d
        return draws

    def depart(self, name: str, years: int) -> None:
        m = next(x for x in self.members if x.name == name)
        self.members.remove(m)
        self.leaving[name] = (m.capital / years, years)

    def pay_departures(self) -> float:
        paid = 0.0
        for k, (a, n) in list(self.leaving.items()):
            paid += a
            if n <= 1:
                del self.leaving[k]
            else:
                self.leaving[k] = (a, n - 1)
        return paid


def own_funds_requirement(fixed_overheads, dtf_cash, dtf_deriv, npr, permanent=0.75,
                          k_dtf_cash=0.001, k_dtf_deriv=0.0001):
    """Highest of the permanent minimum, a quarter of the preceding year's fixed overheads, and the K-factor
    requirement (coefficients on the average daily trading flow in cash and derivatives, plus a net-position
    charge npr). Returns the requirement and which of the three binds."""
    parts = {"permanent": permanent, "fixed overheads": 0.25 * fixed_overheads,
             "K-factors": k_dtf_cash * dtf_cash + k_dtf_deriv * dtf_deriv + npr}
    which = max(parts, key=parts.get)
    return parts[which], which


def steady_spend_share(g: float, d: float) -> float:
    """Spending, as a share of the firm's technology stock, that keeps its stock growing at the competitors'
    rate g when the stock depreciates at d: T' = (1 - d) T + s = (1 + g) T  ->  s = (g + d) T."""
    return g + d


def capture(rel, c0: float, eta: float):
    """Capture per unit traded when the firm's technology relative to its competitors is rel (1 = parity)."""
    return c0 * np.asarray(rel, float) ** eta


@dataclass(frozen=True)
class Params:
    years: int = 10
    capital0: float = 200.0        # trading capital at the start
    margin: float = 0.004          # capital needed per unit of daily volume (a prime broker's requirement)
    days: float = 250.0
    market: float = 400_000.0      # daily volume the firm's markets can give it at most
    c0: float = 1.0e-4             # capture per unit traded at technology parity (1 bp)
    eta: float = 1.0
    g: float = 0.15                # competitors' technology growth
    d: float = 0.20                # depreciation of the firm's technology stock
    tech0: float = 100.0           # the firm's technology stock at the start (parity)
    spend_share: float = 0.35      # technology spending as a share of the stock
    people: float = 60.0           # fixed pay and other fixed costs a year
    var_pay: float = 0.25          # variable pay per unit of profit before variable pay
    market_growth: float = 0.0     # growth of the market's size per year


def simulate(p: Params, retention) -> dict:
    """Run the firm for p.years. Each year: volume = min(capital / margin, market); capture from relative
    technology; profit before variable pay = revenue - people - technology spending; variable pay on a positive
    result; the rest split into retention (added to capital) and payout. `retention` is a ratio, or a function
    of (year, capital, params) returning one (for example a target-capital policy)."""
    cap, tech, front = p.capital0, p.tech0, p.tech0
    keys = ("capital", "volume", "capture", "revenue", "spend", "profit", "payout", "rel")
    out = {k: np.zeros(p.years) for k in keys}
    for t in range(p.years):
        spend = p.spend_share * tech
        rel = tech / front
        vol = min(cap / p.margin, p.market * (1 + p.market_growth) ** t)
        c = float(capture(rel, p.c0, p.eta))
        rev = c * vol * p.days
        pre = rev - p.people - spend
        prof = pre - p.var_pay * max(pre, 0.0)
        r = retention(t, cap, p) if callable(retention) else retention
        pay = (1 - r) * max(prof, 0.0)
        cap += prof - pay
        for k, v in (("capital", cap), ("volume", vol), ("capture", c), ("revenue", rev), ("spend", spend),
                     ("profit", prof), ("payout", pay), ("rel", rel)):
            out[k][t] = v
        tech = (1 - p.d) * tech + spend
        front = (1 + p.g) * front
    return out


def target_capital(target: float):
    """Retain everything until capital reaches `target`, then pay out everything above it."""
    def policy(t, cap, p):
        return 1.0 if cap < target else 0.0
    return policy


def discounted_payout(sim: dict, rate: float, terminal_multiple: float = 0.0) -> float:
    """Present value of the payouts, plus a terminal value of the last year's payout times a multiple."""
    pay = sim["payout"]
    disc = (1 + rate) ** -np.arange(1, len(pay) + 1)
    return float((pay * disc).sum() + terminal_multiple * pay[-1] * disc[-1])
