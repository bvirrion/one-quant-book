"""One Quant Book 17, chapter 3: the options market-making houses, from their own statements.

data/industry/lineage.csv: firms and the trading floors their founders came from (firm.lineage), each row sourced.
data/industry/optiver_results.csv: one privately owned options house's published results, 2023-2025 (EUR million).
data/industry/lca_options.csv: fiscal 2025 filings of the three options houses among the sourced employers against the
other market makers (derived from chapter 14's cache by in_lca_options_derive.py).
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/lineage"))
import firm_lineage as fl  # noqa: E402

DATA = ROOT / "data/industry"


def graph():
    return fl.Graph.load(DATA / "lineage.csv")


def results():
    with open(DATA / "optiver_results.csv") as f:
        return [{k: (float(v) if v else None) for k, v in r.items()} for r in csv.DictReader(f)]


def metrics():
    """Growth, margin, return on average equity and income per head, by year (from the published results)."""
    rs = results()
    out = {}
    for prev, cur in zip(rs[:-1], rs[1:], strict=True):
        y = int(cur["year"])
        out[y] = dict(nti_growth=cur["net_trading_income"] / prev["net_trading_income"] - 1,
                      profit_growth=cur["net_profit"] / prev["net_profit"] - 1,
                      margin=cur["net_profit"] / cur["net_trading_income"],
                      roe=cur["net_profit"] / ((cur["total_equity"] + prev["total_equity"]) / 2))
        e = cur["employees_low"]
        # "more than 2,000 employees" gives an upper bound on income per head; "2,100" a point
        out[y]["nti_per_head_max"] = cur["net_trading_income"] / e if e else None
    return out


def options_pay():
    with open(DATA / "lca_options.csv") as f:
        return {(r["role"], r["group"]): {k: (float(v) if v not in ("", None) else None) for k, v in r.items()
                                          if k not in ("role", "group")} for r in csv.DictReader(f)}
