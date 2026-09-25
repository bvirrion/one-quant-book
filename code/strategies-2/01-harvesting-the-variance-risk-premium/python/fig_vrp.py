"""Chart data for Book 9, chapter 1 (deterministic)."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_vrp import DATA, paths  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(DATA / "vrp_rolling.csv") as fh, open(OUT / "gap.csv", "w") as f:
    f.write("year,gap_pts\n")
    for row in csv.DictReader(fh):
        y, m = int(row["month_end"][:4]), int(row["month_end"][5:7])
        f.write(f"{y + (m - 0.5) / 12:.3f},{100 * float(row['gap12']):.3f}\n")

p = paths()
with open(OUT / "paths.csv", "w") as f:
    f.write("year," + ",".join(f"v{int(100 * k)}" for k in p) + "\n")
    n = len(next(iter(p.values())))
    for i in range(n):
        f.write(f"{(i + 1) * 21 / 252:.3f}," + ",".join(f"{max(p[k][i], 1e-3):.5f}" for k in p) + "\n")
