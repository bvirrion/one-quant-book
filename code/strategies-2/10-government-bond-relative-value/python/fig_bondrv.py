"""Chart data for Book 9, chapter 10 (deterministic)."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_bondrv import DATA, decay  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(DATA / "ust_fly_monthly.csv") as fh, open(OUT / "fly.csv", "w") as f:
    f.write("year,fly\n")
    for row in csv.DictReader(fh):
        y, m = int(row["month"][:4]), int(row["month"][5:7])
        f.write(f"{y + (m - 0.5) / 12:.3f},{float(row['fly']):.1f}\n")

hs = (1, 2, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120)
d = decay(hs)
with open(OUT / "decay.csv", "w") as f:
    f.write("h,slope,planted,fast\n")
    for h in hs:
        f.write(f"{h},{d[h]['slope']:.4f},{d[h]['planted']:.4f},{d[h]['fast']:.4f}\n")
