"""Derive data/industry/lca_kind_gap.csv from chapter 14's cached LCA records (no raw file re-read).

    .venv/bin/python in_lca_kind_gap_derive.py /path/to/lca_dir      # the directory holding kept.csv

Software-developer filings (SOC 15-1252; fiscal 2021's 15-1132 and 15-1133 merged by the 2018 crosswalk) at the
trading firms (market makers, systematic funds, multi-manager platforms) against banks and against exchanges, overall
and by wage level: n and employers on each side, the two medians, and the ratio and difference of medians with 95%
bootstrap intervals (firm.roles.median_gap). A comparison is written only when both sides have ten filings from three
or more employers. Aggregates only.
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

TRADING = ("market maker", "systematic fund", "multi-manager platform")
LEVELS = ("I", "II", "III", "IV")


def main(lca_dir):
    rows = [r for r in lca.kept(lca_dir) if socd.soc(r["soc"]) == "15-1252"]
    rng = np.random.default_rng(20)
    with open(ROOT / "data/industry/lca_kind_gap.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["fy", "versus", "level", "n_trading", "emp_trading", "n_other", "emp_other", "median_trading",
                    "median_other", "ratio", "ratio_lo", "ratio_hi", "diff", "diff_lo", "diff_hi"])
        for fy in (2021, 2025):
            for other in ("bank", "exchange"):
                for lvl in ("all",) + LEVELS:
                    a = [r for r in rows if r["fy"] == fy and r["kind"] in TRADING and lvl in ("all", r["level"])]
                    b = [r for r in rows if r["fy"] == fy and r["kind"] == other and lvl in ("all", r["level"])]
                    ea, eb = len({r["employer"] for r in a}), len({r["employer"] for r in b})
                    if min(ea, eb) < lca.MIN_EMPLOYERS:
                        continue
                    g = fr.median_gap([r["wage"] for r in a], [r["wage"] for r in b], rng)
                    if g is None:
                        continue
                    w.writerow([fy, other, lvl, len(a), ea, len(b), eb,
                                round(float(np.median([r["wage"] for r in a]))),
                                round(float(np.median([r["wage"] for r in b]))),
                                f"{g['ratio']:.4f}", f"{g['ratio_lo']:.4f}", f"{g['ratio_hi']:.4f}",
                                round(g["diff"]), round(g["diff_lo"]), round(g["diff_hi"])])


if __name__ == "__main__":
    main(sys.argv[1])
