"""One Quant Book 16, chapter 1: the economics of a trading firm, read from public filings.

Three firms of three business models, each mapped onto firm.firmecon's standard lines:
  - an electronic market maker (Virtu Financial, Forms 10-K 2019-2025);
  - a listed quantitative asset manager (Man Group, results for 2020-2025, its 'core' measures);
  - a bank's markets division (Goldman Sachs, Global Banking & Markets segment, Form 10-K 2025: 2023-2025).
Figures in $ millions from data/desk/filings_*.csv (derived tables, sources in data/desk/LICENSES.md).
"""
import csv
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/firmecon"))
import firm_firmecon as fe  # noqa: E402

DATA = ROOT / "data/desk"

# Standard lines. Volume-driven costs: fees, clearing and order flow, and the financing of positions
# (Virtu's interest and dividends expense); Man's asset-servicing costs scale with assets.
MAP_VIRTU = {
    "net_revenue": [("trading_income", 1), ("commissions_tech", 1), ("interest_div_income", 1),
                    ("brokerage_fees", -1), ("interest_div_expense", -1)],
    "volume_cost": [("brokerage_fees", 1), ("interest_div_expense", 1)],
    "comp": [("comp", 1)],
    "other_fixed": [("comm_data", 1), ("ops_admin", 1), ("dep_amort", 1)],
}
MAP_MAN = {
    "net_revenue": [("net_revenue", 1), ("asset_servicing", -1)],
    "volume_cost": [("asset_servicing", 1)],
    "comp": [("comp", 1)],
    "other_fixed": [("other_costs", 1), ("other_employment", 1)],
}
MAP_GS = {  # the segment does not split out volume-driven fees: all its revenue counts as net
    "net_revenue": [("net_revenues", 1), ("provision", -1)],
    "comp": [("comp", 1)],
    "other_fixed": [("other_opex", 1)],
}
FIRMS = {"virtu": ("filings_virtu.csv", MAP_VIRTU, "employees", "equity"),
         "man": ("filings_man.csv", MAP_MAN, "headcount", None),
         "gsgbm": ("filings_gsgbm.csv", MAP_GS, None, None)}
LABEL = {"virtu": "market maker", "man": "asset manager", "gsgbm": "bank markets"}


def rows(name):
    with open(DATA / name) as f:
        return list(csv.DictReader(f))


def sts(firm):
    name, mapping, hc, eq = FIRMS[firm]
    return fe.statements(rows(name), mapping, hc, eq)


def vix():
    return {int(r["year"]): float(r["vix_mean"]) for r in rows("vix_annual.csv")}


def table(firm):
    """Per year: net revenue, comp, other fixed, operating profit, ratios."""
    s = sts(firm)
    out = []
    for i, st in enumerate(s):
        d = {"year": st.year, "nr": st.net_revenue, "comp": st.comp, "fixed": st.other_fixed,
             "profit": st.operating_profit, "volume": st.volume_cost}
        d.update(fe.ratios(st, s[i - 1].equity if i and st.equity is not None else None))
        out.append(d)
    return out


def pay_fit(firm):
    """OLS of compensation on net revenue over the firm's years: (fixed pay, slope, se of slope)."""
    s = sts(firm)
    a, b, _, sb = fe.fit_line([x.net_revenue for x in s], [x.comp for x in s])
    return a, b, sb


def vix_fit(firm):
    """OLS of net revenue on the year's mean VIX: slope in $ millions per VIX point, se, and correlation."""
    s, v = sts(firm), vix()
    x = np.array([v[st.year] for st in s])
    y = np.array([st.net_revenue for st in s])
    a, b, _, sb = fe.fit_line(x, y)
    return b, sb, float(np.corrcoef(x, y)[0, 1])


def structure(firm, flex=True):
    s = sts(firm)
    cs = fe.cost_structure(s, flex_pay=flex)
    nr = s[-1].net_revenue
    return {"cs": cs, "nr": nr, "fall": fe.breakeven_fall(cs, nr), "lev": fe.operating_leverage(cs, nr)}


def hook():
    """Virtu 2019 against 2020: revenue roughly doubled, pay and technology hardly moved."""
    r = {int(x["year"]): {k: float(v) for k, v in x.items()} for x in rows("filings_virtu.csv")}
    a, b = r[2019], r[2020]
    return {"rev_ratio": b["revenue"] / a["revenue"], "comp_change": b["comp"] / a["comp"] - 1,
            "comm_change": b["comm_data"] / a["comm_data"] - 1, "pretax": (a["pretax"], b["pretax"])}


def latest_shares():
    """Latest year of each firm, costs as shares of revenue (volume-driven, pay, other fixed, profit)."""
    out = {}
    for f in FIRMS:
        st = sts(f)[-1]
        rev = st.revenue
        out[f] = {"volume": st.volume_cost / rev, "comp": st.comp / rev, "fixed": st.other_fixed / rev,
                  "profit": st.operating_profit / rev, "year": st.year}
    return out


def small_firm(nr=100.0, pay_fixed=15.0, pay_var=0.30, other=35.0):
    """The chapter's worked example (Proposition 1.2): a firm of 100 of net revenue."""
    flex = fe.CostStructure(pay_fixed + other, pay_var)
    rigid = fe.CostStructure(pay_fixed + pay_var * nr + other, 0.0)
    return {"profit": float(fe.profit(flex, nr)), "fall_flex": fe.breakeven_fall(flex, nr),
            "fall_rigid": fe.breakeven_fall(rigid, nr), "lev_flex": fe.operating_leverage(flex, nr),
            "lev_rigid": fe.operating_leverage(rigid, nr)}


def virtu_roe(year):
    """Net income (including non-controlling interests) over average total equity, Virtu."""
    r = {int(x["year"]): {k: float(v) for k, v in x.items()} for x in rows("filings_virtu.csv")}
    return r[year]["net_income"] / (0.5 * (r[year - 1]["equity"] + r[year]["equity"]))


def gs_roe(year):
    """Goldman Sachs' reported return on average common equity attributed to the segment."""
    r = {int(x["year"]): {k: float(v) for k, v in x.items()} for x in rows("filings_gsgbm.csv")}
    return r[year]["net_to_common"] / r[year]["avg_equity"], r[year]["roe_pct"] / 100


def man_reported_comp_ratio(year):
    """Man Group's own definition: compensation over core net revenue (before asset-servicing costs)."""
    r = {int(x["year"]): {k: float(v) for k, v in x.items()} for x in rows("filings_man.csv")}
    return r[year]["comp"] / r[year]["net_revenue"]


def profit_curves(changes=None):
    """Operating profit relative to the latest year's, against the relative change of net revenue (flex pay)."""
    changes = np.round(np.arange(-0.6, 0.41, 0.05), 2) if changes is None else np.asarray(changes)
    out = {}
    for f in FIRMS:
        s = structure(f)
        p0 = float(fe.profit(s["cs"], s["nr"]))
        out[f] = fe.cycle(s["cs"], s["nr"], changes) / p0
    return changes, out


def breakeven_in(firm, year):
    """Break-even fall at a given year's revenue, pay flexing at the firm's fitted slope."""
    a, b, _ = pay_fit(firm)
    st = next(s for s in sts(firm) if s.year == year)
    cs = fe.CostStructure(st.comp - b * st.net_revenue + st.other_fixed, b)
    return fe.breakeven_fall(cs, st.net_revenue)
