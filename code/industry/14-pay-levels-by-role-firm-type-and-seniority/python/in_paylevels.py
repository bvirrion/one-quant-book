"""One Quant Book 17, chapter 14: pay levels by role, firm type and seniority, from four public slices.

data/industry/lca_ranges.csv (in_lca_derive.py): offered annual base of certified US labour condition applications of
sourced employers, fiscal years 2021 and 2025, by employer kind, role family and wage level (cells under ten
applications suppressed); oews_finance.csv (in_oews_derive.py): OEWS May 2025 wage percentiles; eba_high_earners.csv:
EU high earners 2024 by business area; staff cost per head from filings (chapters 11-12).
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/paydata"))
sys.path.insert(0, str(ROOT / "code/firm/bankmix"))
import firm_bankmix as bm  # noqa: E402
import firm_paydata as pd  # noqa: E402

DATA = ROOT / "data/industry"
KINDS = ("systematic fund", "multi-manager platform", "market maker", "bank", "exchange")
ROLES = ("quant researcher", "trader", "quant developer", "software engineer", "ml and data", "risk")
GBP_USD_2024 = None  # set from the ECB table on first use

# staff cost per head from filings, US dollars (chapters 11-12 and ledger F11)
STAFF_PER_HEAD = {
    "market maker": ("Jane Street UK Partnership LLP, 2023-2025", [494.184e6 / 636, 860.089e6 / 688, 1664.536e6 / 790]),
    "systematic fund": ("Quadrature Capital Limited, year to January 2025", [556.120e6 / 173]),  # GBP, converted below
    "bank": ("Goldman Sachs, 2023-2025 (whole firm)", [15499e6 / 45300, 16706e6 / 46500, 18906e6 / 47400]),
}


def ranges():
    out = {}
    with open(DATA / "lca_ranges.csv") as f:
        for r in csv.DictReader(f):
            k = (int(r["fy"]), r["kind"], r["role"], r["level"])
            out[k] = {"n": int(r["n"]), "employers": int(r["employers"]), "suppressed": r["suppressed"] == "1"} | (
                {} if r["suppressed"] == "1" else {c: float(r[c]) for c in ("p10", "p25", "p50", "p75", "p90", "lo50",
                                                                            "hi50")})
    return out


def counts():
    with open(DATA / "lca_counts.csv") as f:
        return {(int(r["fy"]), r["kind"]): (int(r["applications"]), int(r["employers"])) for r in csv.DictReader(f)}


def oews():
    with open(DATA / "oews_finance.csv") as f:
        return {(r["naics"], r["occ"]): r for r in csv.DictReader(f)}


def eba():
    with open(DATA / "eba_high_earners.csv") as f:
        return {(r["institutions"], r["business_area"]): r for r in csv.DictReader(f)}


def gbp_usd(year=2024):
    return bm.load_fx(DATA / "ecb_fx_annual.csv")[year]["GBP"]


def staff_per_head():
    out = {}
    for kind, (label, vals) in STAFF_PER_HEAD.items():
        v = [x * gbp_usd(2024) for x in vals] if kind == "systematic fund" else list(vals)
        out[kind] = (label, min(v), max(v))
    return out


def implied_ratios(fy=2025):
    """Staff cost per head over the LCA median offered base of the same kind (all roles, all levels)."""
    rg = ranges()
    out = {}
    for kind, (label, lo, hi) in staff_per_head().items():
        med = rg[(fy, kind, "all", "all")]["p50"] if (fy, kind, "all", "all") in rg else None
        out[kind] = dict(source=label, lo=lo, hi=hi, base=med, r_lo=lo / med, r_hi=hi / med)
    return out


def growth(kind, role, level="all"):
    rg = ranges()
    a, b = rg.get((2021, kind, role, level)), rg.get((2025, kind, role, level))
    if not a or not b or a.get("suppressed") or b.get("suppressed"):
        return None
    return b["p50"] / a["p50"] - 1


def median_ratios():
    """Pay-ratio median employee against mean staff cost per head (company facts), 2025."""
    out = {}
    with open(DATA / "pay_ratio_medians.csv") as f:
        for r in csv.DictReader(f):
            med = float(r["median_employee_usd"])
            mean = float(r["staff_cost_m"]) * 1e6 / float(r["headcount"]) if r["staff_cost_m"] else None
            out[r["firm"]] = dict(median=med, mean=mean, ratio=None if mean is None else mean / med)
    return out


def eur_usd(year=2025):
    return bm.load_fx(DATA / "ecb_fx_annual.csv")[year]["EUR"]


def evidence():
    """Every source as a PayEvidence record, for the chapter's comparison table."""
    o, rg, e = oews(), ranges(), eba()
    ev = []
    mm = rg[(2025, "market maker", "all", "all")]
    ev.append(pd.PayEvidence("DOL labour condition applications", "offered base (annual)", "sponsored positions at 12 "
                             "market makers, FY2025", 2025, mm["p25"], mm["p75"], "USD", "base only; sponsored staff"))
    s = o[("523000", "15-1252")]
    ev.append(pd.PayEvidence("BLS OEWS May 2025", "wage (excludes nonproduction bonuses)", "software developers, "
                             "securities industry", 2025, float(s["p25"]), float(s["p75"]), "USD", "survey; top-coded"))
    ib = e[("credit institutions", "Investment banking")]
    ev.append(pd.PayEvidence("EBA high earners", "total pay of those paid EUR 1m or more", "EU investment banking",
                             2024, float(ib["avg_total_eur"]), float(ib["avg_total_eur"]), "EUR", "the tail only"))
    return ev


if __name__ == "__main__":
    rg = ranges()
    for k in sorted(rg):
        if k[3] == "all":
            print(k, {a: round(b) for a, b in rg[k].items() if a != "suppressed"}, rg[k]["suppressed"])
    print(counts())
    print(implied_ratios())
