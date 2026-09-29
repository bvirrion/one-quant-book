"""Derive the occupation-code tables of Book 17, chapter 19, from chapter 14's cached LCA records (no raw file re-read).

    .venv/bin/python in_lca_soc_derive.py /path/to/lca_dir      # the directory holding kept.csv (chapter 14's cache)

Writes, from the certified full-time applications of the sourced finance employers already kept by in_lca_derive.py:
  data/industry/lca_soc.csv      fiscal year x scope (all finance employers, or one employer kind) x SOC code x wage
                                 level: n, employers, suppressed, percentiles of offered base and the median's
                                 bootstrap interval (suppressed under ten applications or three employers)
  data/industry/lca_soc_gap.csv  fiscal year x wage level: median of software-developer filings (15-1252; SOC 2010
                                 15-1132 and 15-1133 in fiscal 2021, merged by the 2018 crosswalk) minus median of
                                 financial-quantitative-analyst filings (13-2099.01), and their ratio, with bootstrap
                                 intervals (firm.roles.median_gap)
Aggregates only: no employer-level figure.
"""
import csv
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/industry/14-pay-levels-by-role-firm-type-and-seniority/python"))
sys.path.insert(0, str(ROOT / "code/firm/roles"))
sys.path.insert(0, str(ROOT / "code/firm/paydata"))
import firm_paydata as pd  # noqa: E402
import firm_roles as fr  # noqa: E402
import in_lca_derive as lca  # noqa: E402

DATA = ROOT / "data/industry"
SOC2010 = {"15-1132": "15-1252", "15-1133": "15-1252"}   # BLS 2010-to-2018 crosswalk (software developers)
CODES = ("15-1252", "13-2099.01", "15-2041", "15-2051", "13-2054")
LEVELS = ("I", "II", "III", "IV")


def soc(code):
    c = str(code).strip()
    c = c[:-3] if c.endswith(".00") else c
    return SOC2010.get(c, c)


def main(lca_dir):
    rows = lca.kept(lca_dir)
    rng = np.random.default_rng(19)
    groups = {}
    for r in rows:
        s = soc(r["soc"])
        if s not in CODES:
            continue
        for scope in (r["kind"], "all finance"):
            for lvl in (r["level"], "all"):
                groups.setdefault((r["fy"], scope, s, lvl), []).append((r["wage"], r["employer"]))
    with open(DATA / "lca_soc.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["fy", "scope", "soc", "level", "n", "employers", "suppressed", "p10", "p25", "p50", "p75", "p90",
                    "lo50", "hi50"])
        for key in sorted(groups):
            if key[3] not in LEVELS + ("all",):
                continue
            emps = len({e for _, e in groups[key]})
            c = pd.cell([x for x, _ in groups[key]], rng, 2000)
            if c.get("suppressed") or emps < lca.MIN_EMPLOYERS:
                w.writerow([*key, c["n"], emps, 1] + [""] * 7)
            else:
                w.writerow([*key, c["n"], emps, 0] + [round(c[k]) for k in ("p10", "p25", "p50", "p75", "p90", "lo50",
                                                                       "hi50")])
    with open(DATA / "lca_soc_gap.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["fy", "level", "n_dev", "n_quant", "median_dev", "median_quant", "diff", "diff_lo", "diff_hi",
                    "ratio", "ratio_lo", "ratio_hi"])
        for fy in (2021, 2025):
            for lvl in ("all",) + LEVELS:
                dev = groups.get((fy, "all finance", "15-1252", lvl), [])
                qa = groups.get((fy, "all finance", "13-2099.01", lvl), [])
                ok = all(len({e for _, e in g}) >= lca.MIN_EMPLOYERS for g in (dev, qa))
                g = fr.median_gap([x for x, _ in dev], [x for x, _ in qa], rng) if ok else None
                if g is None:
                    continue
                w.writerow([fy, lvl, len(dev), len(qa), round(float(np.median([x for x, _ in dev]))),
                            round(float(np.median([x for x, _ in qa]))), round(g["diff"]), round(g["diff_lo"]),
                            round(g["diff_hi"]), f"{g['ratio']:.4f}", f"{g['ratio_lo']:.4f}", f"{g['ratio_hi']:.4f}"])


if __name__ == "__main__":
    main(sys.argv[1])
