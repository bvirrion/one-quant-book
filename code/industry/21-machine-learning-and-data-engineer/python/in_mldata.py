"""One Quant Book 17, chapter 21: machine-learning and data roles -- growth of the filings and pay.

Counts: chapter 14's lca_ranges.csv (applications per role family, fiscal 2021 and 2025, all sourced finance employers);
growth by firm.roles.filing_trend with Poisson intervals. Pay: lca_soc.csv and lca_ds_gap.csv (data scientists against
software developers, derived from chapter 14's cache by in_lca_ds_derive.py); the survey's data scientists by industry.
Counts of filings measure hiring of foreign skilled workers by these employers, not employment.
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/roles"))
import firm_roles as fr  # noqa: E402

DATA = ROOT / "data/industry"
FAMILIES = ("ml and data", "software engineer", "quant developer", "risk", "quant researcher", "trader")
LEVELS = ("I", "II", "III", "IV")
SECTORS = ("52", "51", "54")
INDUSTRIES = ("5220A1", "524100", "523000", "513200", "518200", "541500", "551100")


def _read(name):
    with open(DATA / name) as f:
        return list(csv.DictReader(f))


def counts():
    out = {}
    for r in _read("lca_ranges.csv"):
        if r["level"] == "all":
            key = (int(r["fy"]), r["role"])
            out[key] = out.get(key, 0) + int(r["n"])
    return out


def trends():
    c = counts()
    return {f: fr.filing_trend([2021, 2025], [c[(2021, f)], c[(2025, f)]]) for f in FAMILIES}


def shares():
    c = counts()
    tot = {fy: c[(fy, "all")] for fy in (2021, 2025)}
    return tot, {fy: c[(fy, "ml and data")] / tot[fy] for fy in (2021, 2025)}


def by_kind(role="ml and data"):
    return {(int(r["fy"]), r["kind"]): int(r["n"]) for r in _read("lca_ranges.csv")
            if r["role"] == role and r["level"] == "all"}


def gaps():
    return {r["level"]: {k: float(v) for k, v in r.items() if k not in ("fy", "level")}
            for r in _read("lca_ds_gap.csv")}


def survey(occ="15-2051"):
    return {r["naics"]: r for r in _read("oews_roles.csv") if r["occ"] == occ}


if __name__ == "__main__":
    c = counts()
    for f in FAMILIES:
        print(f, c[(2021, f)], c[(2025, f)], fr.poisson_interval(c[(2025, f)]))
    for f, t in trends().items():
        print(f, {k: round(v, 4) for k, v in t.items()})
    print(shares())
    print(by_kind())
    print(gaps())
    s = survey()
    for k in SECTORS + INDUSTRIES:
        print(k, s[k]["industry"], s[k]["employment"], s[k]["p50"])
