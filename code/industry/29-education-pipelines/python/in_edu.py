"""One Quant Book 17, chapter 29: education pipelines -- degrees, placement reports and the filings.

Degrees: data/industry/ipeds_completions.csv (derived by in_ipeds_derive.py from the NCES completions files, public
domain). Placement reports: data/industry/placement_reports.csv (two programmes' own reports, ledger F3-F4). Filings:
chapter 14's lca_ranges.csv (quantitative researcher and quant developer families, fiscal 2025).
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/edupipe"))
import firm_edupipe as fe  # noqa: E402

DATA = ROOT / "data/industry"
FIELDS = ("financial mathematics", "financial analytics", "statistics", "mathematics", "computer science", "physics")
FINANCIAL = ("financial mathematics", "financial analytics")


def completions():
    with open(DATA / "ipeds_completions.csv") as f:
        return {(int(r["year"]), r["field"], r["level"]): int(r["awards"]) for r in csv.DictReader(f)}


def reports():
    out = []
    with open(DATA / "placement_reports.csv") as f:
        for r in csv.DictReader(f):
            out.append(fe.PlacementReport(r["programme"], r["cohort"], int(r["students"]) if r["students"] else None,
                                          int(r["seeking"]), int(r["accepted"]),
                                          int(r["reporting"]) if r["reporting"] else None, float(r["median_base"]),
                                          r["standard"]))
    return out


def quant_filings(fy=2025):
    n = 0
    with open(DATA / "lca_ranges.csv") as f:
        for r in csv.DictReader(f):
            if int(r["fy"]) == fy and r["level"] == "all" and r["role"] in ("quant researcher", "quant developer"):
                n += int(r["n"])
    return n


def named(year=2024):
    c = completions()
    masters = sum(c[(year, f, "master")] for f in FINANCIAL)
    return masters, quant_filings(), masters / quant_filings()


if __name__ == "__main__":
    c = completions()
    for f in FIELDS:
        print(f, [c[(y, f, "master")] for y in (2010, 2014, 2019, 2024)], c[(2024, f, "bachelor")],
              c[(2024, f, "doctorate (research)")])
    print(named())
    for r in reports():
        print(r.programme, r.placement_rate, r.reporting_rate, r.median_quantile_bounds())
