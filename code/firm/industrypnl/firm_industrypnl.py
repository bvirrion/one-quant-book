"""firm.industrypnl -- a firm-year panel of filed revenue and headcount (build of One Quant Book 17, chapter 12).

Each row of the panel is one filer in one year: its revenue after pass-through costs, as the filer reports it or as
the chapter derives it from filed lines, in the filer's currency; its headcount and the basis of the count (at the
year end, or the year's average); its kind of business; and the source of each cell. The module converts revenue to
US dollars at the year's average rate and to constant dollars of a base year with a consumer price index, computes
revenue per head, summarises it by kind and year, and fits the panel regression of the chapter:

    log(revenue per head)_it = a_i + b_k(i) * log(volatility)_t + e_it

with a fixed effect a_i per firm and one slope b_k per kind of firm, by least squares; b_k is the elasticity of
revenue per head to the market's volatility for firms of kind k. Standard errors are the classical ones from the
residual variance; with few firms and years they are indicative, and the chapter says so. NumPy only.

API (stable):
    Row(firm, kind, year, currency, revenue, employees, basis, source)
    load_panel(path) -> list[Row]
    load_fx(path) -> {year: {currency: USD per unit}}          (the ECB table of chapter 7)
    load_cpi(path) -> {year: index}
    real_usd(row, fx, cpi, base) -> revenue in base-year US dollars
    per_head(rows, fx, cpi, base) -> list[dict(firm, kind, year, rph, employees)]
    ranges(ph) -> {(kind, year): (min, max, n)}
    ratio(ph, firm, y1, y0) -> rph in y1 / rph in y0
    fe_fit(ph, x, kinds=None) -> {kind: (b, se)}, plus 'n', 'firms', 'dof', 'r2_within'
"""
import csv
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "bankmix"))
import firm_bankmix as bm  # noqa: E402


@dataclass(frozen=True)
class Row:
    firm: str
    kind: str
    year: int
    currency: str
    revenue: float       # millions, filer's currency, after pass-through costs
    employees: float
    basis: str           # 'year end' or 'average'
    source: str


def load_panel(path):
    with open(path) as f:
        return [Row(r["firm"], r["kind"], int(r["year"]), r["currency"], float(r["revenue_m"]), float(r["employees"]),
                    r["basis"], r["source"]) for r in csv.DictReader(f) if r["revenue_m"] and r["employees"]]


def load_fx(path):
    return bm.load_fx(path)


def load_cpi(path):
    with open(path) as f:
        return {int(r["year"]): float(r["cpi"]) for r in csv.DictReader(f)}


def real_usd(row: Row, fx, cpi, base: int) -> float:
    return row.revenue * fx[row.year][row.currency] * cpi[base] / cpi[row.year]


def per_head(rows, fx, cpi, base):
    return [dict(firm=r.firm, kind=r.kind, year=r.year, employees=r.employees,
                 rph=real_usd(r, fx, cpi, base) / r.employees) for r in rows]


def ranges(ph):
    out = {}
    for p in ph:
        k = (p["kind"], p["year"])
        lo, hi, n = out.get(k, (math.inf, -math.inf, 0))
        out[k] = (min(lo, p["rph"]), max(hi, p["rph"]), n + 1)
    return out


def ratio(ph, firm, y1, y0):
    v = {p["year"]: p["rph"] for p in ph if p["firm"] == firm}
    return v[y1] / v[y0]


def fe_fit(ph, x, kinds=None):
    """Least squares of log rph on firm dummies and log(x[year]) interacted with kind."""
    ph = [p for p in ph if p["year"] in x and (kinds is None or p["kind"] in kinds)]
    firms = sorted({p["firm"] for p in ph})
    ks = sorted({p["kind"] for p in ph})
    n, nf, nk = len(ph), len(firms), len(ks)
    X = np.zeros((n, nf + nk))
    y = np.empty(n)
    for i, p in enumerate(ph):
        X[i, firms.index(p["firm"])] = 1.0
        X[i, nf + ks.index(p["kind"])] = math.log(x[p["year"]])
        y[i] = math.log(p["rph"])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    dof = n - nf - nk
    s2 = float(resid @ resid) / dof
    cov = s2 * np.linalg.pinv(X.T @ X)
    # within R^2: share of the variance left after firm means explained by the slopes
    dm = y.copy()
    for f in firms:
        idx = [i for i, p in enumerate(ph) if p["firm"] == f]
        dm[idx] -= y[idx].mean()
    r2 = 1.0 - float(resid @ resid) / float(dm @ dm)
    out = {k: (float(beta[nf + j]), float(math.sqrt(cov[nf + j, nf + j]))) for j, k in enumerate(ks)}
    out.update(n=n, firms=nf, dof=dof, r2_within=r2)
    return out
