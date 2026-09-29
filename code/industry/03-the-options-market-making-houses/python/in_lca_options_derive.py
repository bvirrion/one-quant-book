"""Derive data/industry/lca_options.csv from chapter 14's cached LCA records (no raw file re-read; run in Phase C).

    .venv/bin/python in_lca_options_derive.py /path/to/lca_dir      # the directory holding kept.csv

Fiscal 2025 filings of the market makers, split into the three options houses among the sourced employers (Optiver,
IMC, Susquehanna; chapter 3's firms) and the other market makers: counts, employers, percentiles of offered base and
the median's bootstrap interval by role family, with the ten-filing and three-employer rule, and the difference of the
two groups' medians with its bootstrap interval (firm.roles.median_gap); and data/industry/lca_options_levels.csv, the
number of each group's filings at each wage level. Aggregates only; no employer-level figure.
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

OPTIONS = ("Optiver", "IMC", "Susquehanna")
ROLES = ("all", "quant researcher", "software engineer", "trader")


def main(lca_dir):
    rows = [r for r in lca.kept(lca_dir) if r["fy"] == 2025 and r["kind"] == "market maker"]
    rng = np.random.default_rng(3)
    with open(ROOT / "data/industry/lca_options.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["fy", "role", "group", "n", "employers", "suppressed", "p10", "p25", "p50", "p75", "p90", "lo50",
                    "hi50", "diff", "diff_lo", "diff_hi"])
        for role in ROLES:
            sel = [r for r in rows if role in ("all", r["role"])]
            groups = {"options houses": [r for r in sel if r["employer"] in OPTIONS],
                      "other market makers": [r for r in sel if r["employer"] not in OPTIONS]}
            ok = all(len({r["employer"] for r in g}) >= lca.MIN_EMPLOYERS for g in groups.values())
            g = fr.median_gap([r["wage"] for r in groups["options houses"]],
                              [r["wage"] for r in groups["other market makers"]], rng) if ok else None
            for name, grp in groups.items():
                emps = len({r["employer"] for r in grp})
                c = pd.cell([r["wage"] for r in grp], rng, 2000)
                gap = ["", "", ""] if g is None or name != "options houses" else [round(g["diff"]), round(g["diff_lo"]),
                                                                                 round(g["diff_hi"])]
                if c.get("suppressed") or emps < lca.MIN_EMPLOYERS:
                    w.writerow([2025, role, name, c["n"], emps, 1] + [""] * 7 + gap)
                else:
                    w.writerow([2025, role, name, c["n"], emps, 0]
                               + [round(c[k]) for k in ("p10", "p25", "p50", "p75", "p90", "lo50", "hi50")] + gap)

    with open(ROOT / "data/industry/lca_options_levels.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["fy", "group", "level", "n"])
        for name, test in (("options houses", lambda e: e in OPTIONS),
                           ("other market makers", lambda e: e not in OPTIONS)):
            for lvl in ("I", "II", "III", "IV", "none"):
                w.writerow([2025, name, lvl, sum(1 for r in rows if test(r["employer"]) and r["level"] == lvl)])


if __name__ == "__main__":
    main(sys.argv[1])
