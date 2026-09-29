"""One Quant Book 17, chapter 12: revenue and profit across the industry.

data/industry/filings_perhead.csv (written by in_panel_derive.py): one row per filer and year, 2019-2025, revenue after
pass-through costs in millions of the filer's currency, headcount and its basis, the revenue line and the source.
Converted to US dollars at the ECB annual average (data/industry/ecb_fx_annual.csv) and to 2025 dollars with the US
consumer price index (data/industry/cpi_usa.csv, OECD). The volatility measure is the yearly mean of the VIX index's
daily closes, from Book 16's derived table (data/desk/vix_annual.csv, read-only).
"""
import csv
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/industrypnl"))
import firm_industrypnl as ip  # noqa: E402

DATA = ROOT / "data/industry"
BASE = 2025
ENTITY = "UK entity"  # a UK subsidiary of a larger group: shown, never pooled with whole firms
PROFIT = {  # firm: (year, profit in millions of currency, currency, line, employees) -- ledger rows in chapter 12
    "Quadrature Capital Limited": (2024, 556.556, "GBP", "operating profit", 173),
    "CME Group": (2025, 4229.5, "USD", "operating income", 3875),
    "Virtu Financial": (2025, 1094.3, "USD", "income before taxes", 1027),
    "Optiver": (2024, 1369.0, "EUR", "net profit", 2100),
}


def vix():
    with open(ROOT / "data/desk/vix_annual.csv") as f:
        return {int(r["year"]): float(r["vix_mean"]) for r in csv.DictReader(f)}


def fx():
    return ip.load_fx(DATA / "ecb_fx_annual.csv")


def cpi():
    return ip.load_cpi(DATA / "cpi_usa.csv")


def rows():
    return ip.load_panel(DATA / "filings_perhead.csv")


def per_head():
    return ip.per_head(rows(), fx(), cpi(), BASE)


def regression_set(ph=None):
    """Whole firms with a point headcount: UK entities and lower-bound headcounts are left out."""
    ph = ph or per_head()
    bounds = {(r.firm, r.year) for r in rows() if r.basis == "lower bound"}
    return [p for p in ph if p["kind"] != ENTITY and (p["firm"], p["year"]) not in bounds]


def fit(ph=None):
    return ip.fe_fit(regression_set(ph), vix())


def by_firm(ph=None):
    ph = ph or per_head()
    out = {}
    for p in ph:
        out.setdefault(p["firm"], {"kind": p["kind"], "years": {}})["years"][p["year"]] = p["rph"]
    return out


def firm_ranges(ph=None):
    """Per firm: kind, min, max, median over its years, the latest year and its value; sorted by median."""
    out = []
    for f, d in by_firm(ph).items():
        v = d["years"]
        last = max(v)
        out.append(dict(firm=f, kind=d["kind"], lo=min(v.values()), hi=max(v.values()),
                        med=statistics.median(v.values()), last=last, last_v=v[last], n=len(v)))
    return sorted(out, key=lambda r: r["med"])


def spread(ph=None):
    """Across whole firms: lowest and highest revenue per head in the panel, and within-firm swings."""
    fr = [r for r in firm_ranges(ph) if r["kind"] != ENTITY]
    lo = min(fr, key=lambda r: r["lo"])
    hi = max(fr, key=lambda r: r["hi"])
    swings = {r["firm"]: r["hi"] / r["lo"] for r in fr if r["n"] >= 4}
    return dict(lo=(lo["firm"], lo["lo"]), hi=(hi["firm"], hi["hi"]), factor=hi["hi"] / lo["lo"], swings=swings)


def kind_medians(ph=None):
    ph = regression_set(ph)
    out = {}
    for p in ph:
        out.setdefault((p["kind"], p["year"]), []).append(p["rph"])
    return {k: statistics.median(v) for k, v in out.items()}


def mm_ratios(ph=None):
    ph = ph or per_head()
    return {f: ip.ratio(ph, f, 2020, 2023) for f in ("Virtu Financial", "Flow Traders")}


def profit_per_head():
    fxt = fx()
    return {f: dict(year=y, local=p / n, usd=p * fxt[y][c] / n, currency=c, line=line)
            for f, (y, p, c, line, n) in PROFIT.items()}


def entity_rows(ph=None):
    ph = ph or per_head()
    return sorted((p["year"], p["rph"], p["employees"]) for p in ph if p["kind"] == ENTITY)


if __name__ == "__main__":
    for r in firm_ranges():
        print({k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()})
    print(spread())
    print(fit())
    print(mm_ratios())
    print(profit_per_head())
    print(entity_rows())
