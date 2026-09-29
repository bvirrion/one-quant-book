"""Derive the chapter's LCA tables from the DOL disclosure files (run once, late; raw files never committed).

    nice -n 19 systemd-run --user --scope -p MemoryHigh=2G -p MemoryMax=4G \
        .venv/bin/python in_lca_derive.py /path/to/lca_dir

The kept records (fiscal year, employer kind and label, role family, wage level, SOC code, annual wage; no other field)
are cached in lca_dir/kept.csv, so the raw files are streamed once; later runs rebuild the tables from the cache.

Reads LCA_Disclosure_Data_FY2025_Q1..Q4.xlsx and FY2021_Q1..Q4.xlsx one at a time with firm.paydata.read_lca (streamed,
read-only), keeps certified full-time applications of the sourced employers in data/industry/lca_employers.csv whose
job title or SOC code falls in a role family, annualises the lower end of the offered wage, and writes:
  data/industry/lca_ranges.csv   fiscal year x employer kind x role family x wage level: n and percentiles of offered
                                 annual base (cells of fewer than ten applications or fewer than three employers
                                 keep n and are marked suppressed)
  data/industry/lca_titles.csv   FY2025 role family x SOC code: number of applications (ten or more only)
  data/industry/lca_counts.csv   fiscal year x employer kind: applications kept, and the number of employers matched
No employer-level figure, no name of a person, and no contact field is read or written.
"""
import csv
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/paydata"))
import firm_paydata as pd  # noqa: E402

DATA = ROOT / "data/industry"
FILES = {2025: [f"LCA_Disclosure_Data_FY2025_Q{q}.xlsx" for q in (1, 2, 3, 4)],
         2021: [f"LCA_Disclosure_Data_FY2021_Q{q}.xlsx" for q in (1, 2, 3, 4)]}
LEVELS = ("I", "II", "III", "IV")
MIN_EMPLOYERS = 3  # a cell drawn from one or two employers would publish an employer's pay: suppressed


def records(lca_dir, fy, rules):
    seen = set()
    for name in FILES[fy]:
        for d in pd.read_lca(pathlib.Path(lca_dir) / name,
                             keep=lambda d: d.get("CASE_STATUS") == "Certified"
                             and str(d.get("FULL_TIME_POSITION") or "Y").upper().startswith("Y")):
            rule = pd.classify(d.get("EMPLOYER_NAME"), rules)
            if rule is None or d.get("CASE_NUMBER") in seen:
                continue
            role = pd.classify_role(d.get("JOB_TITLE"), d.get("SOC_CODE"))
            wage = pd.annualise(d.get("WAGE_RATE_OF_PAY_FROM"), d.get("WAGE_UNIT_OF_PAY"))
            if role is None or wage is None or wage < 20_000:
                continue
            seen.add(d.get("CASE_NUMBER"))
            lvl = str(d.get("PW_WAGE_LEVEL") or "").strip()
            yield dict(fy=fy, kind=rule.kind, employer=rule.label, role=role, level=lvl if lvl in LEVELS else "none",
                       soc=str(d.get("SOC_CODE") or "").strip(), wage=wage)


def kept(lca_dir):
    cache = pathlib.Path(lca_dir) / "kept.csv"
    fields = ("fy", "kind", "employer", "role", "level", "soc", "wage")
    if not cache.exists():
        rules = pd.load_rules(DATA / "lca_employers.csv")
        with open(cache, "w", newline="") as f:
            w = csv.DictWriter(f, fields, lineterminator="\n")
            w.writeheader()
            for fy in (2025, 2021):
                for r in records(lca_dir, fy, rules):
                    w.writerow(r)
    with open(cache) as f:
        return [dict(r, fy=int(r["fy"]), wage=float(r["wage"])) for r in csv.DictReader(f)]


def main(lca_dir):
    rows = kept(lca_dir)
    rng = np.random.default_rng(14)
    groups = {}
    for r in rows:
        for role in (r["role"], "all"):
            for lvl in (r["level"], "all"):
                groups.setdefault((r["fy"], r["kind"], role, lvl), []).append((r["wage"], r["employer"]))
    with open(DATA / "lca_ranges.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["fy", "kind", "role", "level", "n", "employers", "suppressed", "p10", "p25", "p50", "p75", "p90",
                    "lo50", "hi50"])
        for key in sorted(groups):
            emps = len({e for _, e in groups[key]})
            c = pd.cell([x for x, _ in groups[key]], rng, 2000)
            if c.get("suppressed") or emps < MIN_EMPLOYERS:
                w.writerow([*key, c["n"], emps, 1, "", "", "", "", "", "", ""])
            else:
                w.writerow([*key, c["n"], emps, 0] + [round(c[k]) for k in ("p10", "p25", "p50", "p75", "p90", "lo50",
                                                                       "hi50")])
    titles = {}
    for r in rows:
        if r["fy"] == 2025:
            soc = r["soc"][:-3] if r["soc"].endswith(".00") else r["soc"]
            titles[(r["role"], soc)] = titles.get((r["role"], soc), 0) + 1
    with open(DATA / "lca_titles.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["role", "soc", "n"])
        for (role, soc), n in sorted(titles.items()):
            if n >= pd.MIN_CELL:
                w.writerow([role, soc, n])
    counts = {}
    for r in rows:
        k = (r["fy"], r["kind"])
        c = counts.setdefault(k, [0, set()])
        c[0] += 1
        c[1].add(r["employer"])
    with open(DATA / "lca_counts.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["fy", "kind", "applications", "employers"])
        for (fy, kind), (n, emps) in sorted(counts.items()):
            w.writerow([fy, kind, n, len(emps)])


if __name__ == "__main__":
    main(sys.argv[1])
