"""Derive data/industry/lca_control_gap.csv from chapter 14's cached LCA records (no raw file re-read).

    .venv/bin/python in_lca_control_derive.py /path/to/lca_dir      # the directory holding kept.csv

Control-function filings (the 'risk' title family) against front-office filings (the 'trader' and 'quant researcher'
families) at banks and at the trading firms pooled (market makers, systematic funds, multi-manager platforms), fiscal
2021 and 2025, overall and by wage level: counts, employers, medians, and the ratio and difference of medians with 95%
bootstrap intervals (firm.roles.median_gap); written only when each side has ten filings from three employers.
Aggregates only.
"""
import csv
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/industry/14-pay-levels-by-role-firm-type-and-seniority/python"))
sys.path.insert(0, str(ROOT / "code/firm/roles"))
import firm_roles as fr  # noqa: E402
import in_lca_derive as lca  # noqa: E402

SCOPES = {"bank": ("bank",), "trading firms": ("market maker", "systematic fund", "multi-manager platform")}
FRONT = ("trader", "quant researcher")
LEVELS = ("I", "II", "III", "IV")


def main(lca_dir):
    rows = lca.kept(lca_dir)
    rng = np.random.default_rng(24)
    with open(ROOT / "data/industry/lca_control_gap.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["fy", "scope", "level", "n_control", "emp_control", "n_front", "emp_front", "median_control",
                    "median_front", "ratio", "ratio_lo", "ratio_hi", "diff", "diff_lo", "diff_hi"])
        for fy in (2021, 2025):
            for scope, kinds in SCOPES.items():
                for lvl in ("all",) + LEVELS:
                    sel = [r for r in rows if r["fy"] == fy and r["kind"] in kinds and lvl in ("all", r["level"])]
                    c = [r for r in sel if r["role"] == "risk"]
                    fo = [r for r in sel if r["role"] in FRONT]
                    ec, ef = len({r["employer"] for r in c}), len({r["employer"] for r in fo})
                    if min(ec, ef) < lca.MIN_EMPLOYERS:
                        continue
                    g = fr.median_gap([r["wage"] for r in c], [r["wage"] for r in fo], rng)
                    if g is None:
                        continue
                    mc, mf = float(np.median([r["wage"] for r in c])), float(np.median([r["wage"] for r in fo]))
                    w.writerow([fy, scope, lvl, len(c), ec, len(fo), ef, round(mc), round(mf), f"{g['ratio']:.4f}",
                                f"{g['ratio_lo']:.4f}", f"{g['ratio_hi']:.4f}", round(g["diff"]), round(g["diff_lo"]),
                                round(g["diff_hi"])])


if __name__ == "__main__":
    main(sys.argv[1])
