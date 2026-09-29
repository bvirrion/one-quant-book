"""One Quant Book 17, chapter 9: exchanges and regulators as employers, from filings and published pay scales.

data/industry/infrastructure_employers.csv: four US exchange groups' 2025 revenue, operating income and employees;
data/industry/sec_sk_2026.csv and sec_sk_locality_2026.csv: the SEC's 2026 SK pay scale and locality rates.
data/industry/lca_ranges.csv (chapter 14): offered base by employer kind and role family, fiscal 2025.
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/payband"))
import firm_payband as pb  # noqa: E402

DATA = ROOT / "data/industry"
SEC_CAP = 292300.0


def exchanges():
    with open(DATA / "infrastructure_employers.csv") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        e = float(r["employees"])
        r["revenue_per_head_m"] = float(r["revenue_m"]) / e
        r["op_income_per_head_m"] = float(r["operating_income_m"]) / e
        r["op_margin"] = float(r["operating_income_m"]) / float(r["revenue_m"])
    return rows


def sec():
    return pb.load_scale("SEC SK 2026", DATA / "sec_sk_2026.csv", DATA / "sec_sk_locality_2026.csv", SEC_CAP)


def sec_band(grade, station="New York"):
    return pb.at(sec(), grade, station)


ROLES = ("all", "software engineer", "quant researcher", "ml and data")
KINDS = ("exchange", "bank", "market maker")


def filings(fy=2025):
    with open(DATA / "lca_ranges.csv") as f:
        return {(r["kind"], r["role"]): {"n": int(r["n"]), "employers": int(r["employers"]),
                                         "p50": float(r["p50"]) if r["p50"] else None}
                for r in csv.DictReader(f) if int(r["fy"]) == fy and r["level"] == "all" and r["kind"] in KINDS
                and r["role"] in ROLES}
