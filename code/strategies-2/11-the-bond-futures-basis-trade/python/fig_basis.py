"""Chart data for Book 9, chapter 11 (deterministic)."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_basis import DATA, YEAR, paths  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(DATA / "tff_levfunds.csv") as fh, open(OUT / "tff.csv", "w") as f:
    f.write("year,total\n")
    for row in csv.DictReader(fh):
        y, m, d = (int(x) for x in row["date"].split("-"))
        f.write(f"{y + (m - 1) / 12 + (d - 1) / 365:.3f},{float(row['total']):.1f}\n")

p = paths()
with open(OUT / "capital.csv", "w") as f:
    f.write("year,L10,L20,L50\n")
    for i, d in enumerate(p["day"]):
        f.write(f"{d / YEAR:.3f},{p[10][i]:.4f},{p[20][i]:.4f},{p[50][i]:.4f}\n")
