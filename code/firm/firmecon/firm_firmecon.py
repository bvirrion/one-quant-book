"""firm.firmecon -- the economics of a trading firm (build of One Quant Book 16, chapter 1).

A trading firm's income statement, whatever its business model, is read in five standard lines:

    net trading revenue  = revenue - volume-driven costs   (fees, clearing, order flow, financing of positions)
    compensation         = fixed pay + variable pay
    other fixed costs    = technology, data, premises, administration, depreciation
    operating profit     = net trading revenue - compensation - other fixed costs

A filer's reported lines are mapped onto these by a mapping table (line -> list of (column, sign)). The cost
structure is then estimated from the firm's own history: each cost line regressed on net trading revenue
across years, the intercept being its fixed part and the slope its variable part. With that structure the
chapter asks two questions of every firm: how far can net revenue fall before operating profit is zero
(the break-even fall), and by how much does profit move for a one per cent move in net revenue (operating
leverage). Amounts are in any single currency unit (the book uses millions). NumPy only.

API (stable):
    Statement(year, net_revenue, comp, other_fixed, volume_cost=0.0, headcount=None, equity=None)
    map_lines(row, mapping) -> dict            standard line -> sum of sign * row[column]
    statements(rows, mapping) -> list[Statement]
    ratios(st) -> dict                          comp ratio, operating margin, per-head figures, ROE
    fit_line(x, y) -> (a, b, se_a, se_b)        ordinary least squares y = a + b x
    CostStructure(fixed, var_share)             fixed costs and variable cost per unit of net revenue
    cost_structure(sts, flex_pay=True)          estimated from the firm's own years
    profit(cs, nr), breakeven_fall(cs, nr), operating_leverage(cs, nr)
    cycle(cs, nr, changes) -> array             operating profit after each relative change of net revenue
"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Statement:
    year: int
    net_revenue: float
    comp: float
    other_fixed: float
    volume_cost: float = 0.0
    headcount: float | None = None
    equity: float | None = None

    @property
    def revenue(self) -> float:
        return self.net_revenue + self.volume_cost

    @property
    def operating_profit(self) -> float:
        return self.net_revenue - self.comp - self.other_fixed


def map_lines(row: dict, mapping: dict) -> dict:
    """Sum each standard line from the filer's columns: mapping[line] = [(column, sign), ...]."""
    return {line: float(sum(s * float(row[c]) for c, s in terms)) for line, terms in mapping.items()}


def statements(rows, mapping, headcount=None, equity=None):
    out = []
    for r in rows:
        m = map_lines(r, mapping)
        out.append(Statement(int(r["year"]), m["net_revenue"], m["comp"], m["other_fixed"], m.get("volume_cost", 0.0),
                             float(r[headcount]) if headcount else None, float(r[equity]) if equity else None))
    return out


def ratios(st: Statement, equity_open: float | None = None) -> dict:
    """Compensation ratio (to net revenue), operating margin, per-head figures, return on average equity."""
    d = {"comp_ratio": st.comp / st.net_revenue, "operating_margin": st.operating_profit / st.net_revenue,
         "fixed_cover": st.net_revenue / st.other_fixed}
    if st.headcount:
        d["revenue_per_head"] = st.net_revenue / st.headcount
        d["comp_per_head"] = st.comp / st.headcount
    if st.equity is not None:
        eq = st.equity if equity_open is None else 0.5 * (st.equity + equity_open)
        d["roe_operating"] = st.operating_profit / eq
    return d


def fit_line(x, y):
    """OLS y = a + b x with classical standard errors (needs at least three points)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x)
    if n < 3:
        raise ValueError("need at least three points")
    xm = x.mean()
    sxx = float(((x - xm) ** 2).sum())
    b = float(((x - xm) * (y - y.mean())).sum() / sxx)
    a = float(y.mean() - b * xm)
    res = y - a - b * x
    s2 = float((res ** 2).sum() / (n - 2))
    return a, b, float(np.sqrt(s2 * (1 / n + xm ** 2 / sxx))), float(np.sqrt(s2 / sxx))


@dataclass(frozen=True)
class CostStructure:
    fixed: float          # costs that do not move with net revenue (per year)
    var_share: float      # costs added per unit of net revenue (variable pay, and anything else that scales)


def cost_structure(sts, flex_pay: bool = True) -> CostStructure:
    """Fixed and variable parts from the firm's history. Pay: intercept and slope of comp on net revenue
    (flex_pay) or all fixed at its latest level; other fixed costs: their latest level."""
    last = sts[-1]
    if flex_pay:
        a, b, _, _ = fit_line([s.net_revenue for s in sts], [s.comp for s in sts])
        b = min(max(b, 0.0), 1.0)
        fixed_pay = last.comp - b * last.net_revenue
        return CostStructure(fixed_pay + last.other_fixed, b)
    return CostStructure(last.comp + last.other_fixed, 0.0)


def profit(cs: CostStructure, nr):
    return (1.0 - cs.var_share) * np.asarray(nr, float) - cs.fixed


def breakeven_fall(cs: CostStructure, nr: float) -> float:
    """Relative fall of net revenue that takes operating profit to zero: 1 - F / ((1 - b) NR)."""
    return 1.0 - cs.fixed / ((1.0 - cs.var_share) * nr)


def operating_leverage(cs: CostStructure, nr: float) -> float:
    """Elasticity of operating profit to net revenue: (1 - b) NR / profit."""
    p = float(profit(cs, nr))
    if p <= 0:
        raise ValueError("operating leverage is defined only above break-even")
    return (1.0 - cs.var_share) * nr / p


def cycle(cs: CostStructure, nr: float, changes) -> np.ndarray:
    """Operating profit after each relative change of net revenue (e.g. -0.5 .. +0.5)."""
    return profit(cs, nr * (1.0 + np.asarray(changes, float)))
