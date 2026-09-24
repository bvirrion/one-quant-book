"""Chart data for Book 2, Chapter 25 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from clo_demo import irr_table, paths

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
ps = paths()
cdrs = sorted(ps)
with open(OUT / "paths.csv", "w") as f:
    f.write("quarter," + ",".join(f"oc{i},eq{i}" for i in range(len(cdrs))) + "\n")
    for t in range(len(ps[cdrs[0]])):
        f.write(f"{t + 1}," + ",".join(f"{ps[c][t][2]:.5f},{ps[c][t][3]:.4f}" for c in cdrs) + "\n")
with open(OUT / "irr.csv", "w") as f:
    f.write("cdr,irr,diverted\n")
    for cdr, irr, div in irr_table():
        f.write(f"{100 * cdr:.1f},{100 * irr:.3f},{div:.3f}\n")
