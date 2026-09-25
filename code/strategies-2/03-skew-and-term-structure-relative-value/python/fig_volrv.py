"""Chart data for Book 9, chapter 3 (deterministic)."""
import csv
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_volrv import DATA, books  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(DATA / "term_monthly.csv") as fh, open(OUT / "slope.csv", "w") as f:
    f.write("year,slope,vix\n")
    for row in csv.DictReader(fh):
        y, m = int(row["month"][:4]), int(row["month"][5:7])
        f.write(f"{y + (m - 0.5) / 12:.3f},{float(row['slope']):.2f},{float(row['vix']):.2f}\n")

b = books()["calendar residual"]
sd = b["total"].std()
cum = {k: np.cumsum(b[k]) / sd for k in ("total", "spot_time", "level", "slope")}
with open(OUT / "calendar.csv", "w") as f:
    f.write("year,total,spot_time,level,slope\n")
    for i, s in enumerate(b["start"]):
        f.write(f"{(s + 21) / 252:.3f}," + ",".join(f"{cum[k][i]:.3f}" for k in cum) + "\n")
