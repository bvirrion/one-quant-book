"""firm.bankdesk -- desks of a bank's markets division under several capital constraints
(build of One Quant Book 16, chapter 5).

A desk uses three scarce things the group must hold equity against: risk-weighted assets (a target ratio of
common equity to RWA), leverage exposure (a leverage-ratio requirement), and the loss it would take in the
supervisory stress scenario. Equity is allocated to a desk by one key or by the largest of the three (the
constraint that binds for that desk). A balance-sheet charge prices leverage exposure at the cost of the equity
it requires. The desk mix that maximises the division's profit under the group's constraints is a linear
programme. Amounts in one currency (the chapter uses $ billions), rates as fractions.

API (stable):
    Desk(name, revenue, cost, rwa, le, stress)
    Keys(k_rwa, k_le, tax); allocate(desks, keys) -> dict key -> equity per desk (keys: rwa, leverage, stress, binding)
    roae(desks, equity, tax) -> after-tax return on allocated equity per desk
    binding(desk, keys) -> name of the constraint that binds for the desk
    balance_sheet_charge(desk, rate_per_le, tax) -> after-tax profit after the charge ; breakeven_charge(desk, tax)
    optimal_mix(desks, equity, keys, x_max) -> scale of each desk maximising after-tax profit (scipy linprog)
"""
from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog


@dataclass(frozen=True)
class Desk:
    name: str
    revenue: float
    cost: float
    rwa: float        # risk-weighted assets
    le: float         # leverage exposure
    stress: float     # loss in the supervisory stress scenario

    def profit(self, tax: float) -> float:
        return (self.revenue - self.cost) * (1 - tax)


@dataclass(frozen=True)
class Keys:
    k_rwa: float = 0.13     # common equity held per unit of RWA
    k_le: float = 0.05      # equity held per unit of leverage exposure
    tax: float = 0.25


def allocate(desks, keys: Keys) -> dict:
    rwa = np.array([d.rwa for d in desks]) * keys.k_rwa
    lev = np.array([d.le for d in desks]) * keys.k_le
    st = np.array([d.stress for d in desks])
    return {"rwa": rwa, "leverage": lev, "stress": st, "binding": np.maximum.reduce([rwa, lev, st])}


def roae(desks, equity, tax: float) -> np.ndarray:
    return np.array([d.profit(tax) for d in desks]) / np.asarray(equity, float)


def binding(desk: Desk, keys: Keys) -> str:
    parts = {"rwa": keys.k_rwa * desk.rwa, "leverage": keys.k_le * desk.le, "stress": desk.stress}
    return max(parts, key=parts.get)


def balance_sheet_charge(desk: Desk, rate_per_le: float, tax: float) -> float:
    """After-tax profit after a charge of rate_per_le per unit of leverage exposure (the charge is deductible)."""
    return (desk.revenue - desk.cost - rate_per_le * desk.le) * (1 - tax)


def breakeven_charge(desk: Desk) -> float:
    """The charge per unit of leverage exposure that takes the desk's profit to zero."""
    return (desk.revenue - desk.cost) / desk.le


def optimal_mix(desks, equity: float, keys: Keys, x_max: float = 1.5) -> np.ndarray:
    """Scale x_i in [0, x_max] of each desk (x = 1 today) maximising after-tax profit, subject to the group's
    equity covering the RWA-based and the leverage-based requirements of the whole mix."""
    c = -np.array([d.profit(keys.tax) for d in desks])
    A = np.array([[keys.k_rwa * d.rwa for d in desks], [keys.k_le * d.le for d in desks]])
    res = linprog(c, A_ub=A, b_ub=[equity, equity], bounds=[(0.0, x_max)] * len(desks), method="highs")
    if not res.success:
        raise RuntimeError(res.message)
    return res.x
