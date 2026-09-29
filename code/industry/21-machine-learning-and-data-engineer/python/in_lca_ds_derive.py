"""Derive data/industry/lca_ds_gap.csv from chapter 14's cached LCA records (no raw file re-read).

    .venv/bin/python in_lca_ds_derive.py /path/to/lca_dir      # the directory holding kept.csv

Fiscal 2025 filings at the sourced finance employers coded as data scientists (SOC 15-2051, with O*NET's 15-2051.01)
against those coded as software developers (15-1252), overall and by wage level: counts, employers, medians, and the
difference and ratio of medians with 95% bootstrap intervals (firm.roles.median_gap), written only when each side has
ten filings from three employers. Aggregates only.
"""
import csv
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/industry/14-pay-levels-by-role-firm-type-and-seniority/python"))
sys.path.insert(0, str(ROOT / "code/industry/19-quant-developer/python"))
sys.path.insert(0, str(ROOT / "code/firm/roles"))
import firm_roles as fr  # noqa: E402
import in_lca_derive as lca  # noqa: E402
import in_lca_soc_derive as socd  # noqa: E402

LEVELS = ("I", "II", "III", "IV")


def code(r):
    s = socd.soc(r["soc"])
    return "15-2051" if s.startswith("15-2051") else s


def main(lca_dir):
    rows = [r for r in lca.kept(lca_dir) if r["fy"] == 2025 and code(r) in ("15-2051", "15-1252")]
    rng = np.random.default_rng(21)
    with open(ROOT / "data/industry/lca_ds_gap.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["fy", "level", "n_ds", "emp_ds", "n_dev", "emp_dev", "median_ds", "median_dev", "diff", "diff_lo",
                    "diff_hi", "ratio", "ratio_lo", "ratio_hi"])
        for lvl in ("all",) + LEVELS:
            a = [r for r in rows if code(r) == "15-2051" and lvl in ("all", r["level"])]
            b = [r for r in rows if code(r) == "15-1252" and lvl in ("all", r["level"])]
            ea, eb = len({r["employer"] for r in a}), len({r["employer"] for r in b})
            if min(ea, eb) < lca.MIN_EMPLOYERS:
                continue
            g = fr.median_gap([r["wage"] for r in a], [r["wage"] for r in b], rng)
            if g is None:
                continue
            w.writerow([2025, lvl, len(a), ea, len(b), eb, round(float(np.median([r["wage"] for r in a]))),
                        round(float(np.median([r["wage"] for r in b]))), round(g["diff"]), round(g["diff_lo"]),
                        round(g["diff_hi"]), f"{g['ratio']:.4f}", f"{g['ratio_lo']:.4f}", f"{g['ratio_hi']:.4f}"])


if __name__ == "__main__":
    main(sys.argv[1])
