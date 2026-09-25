"""Chart data for Book 9, chapter 2 (deterministic)."""
import csv
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_dispersion import DATA, TENOR, monthly  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(DATA / "cor_monthly.csv") as fh, open(OUT / "cor1m.csv", "w") as f:
    f.write("year,cor1m\n")
    for row in csv.DictReader(fh):
        y, m = int(row["month"][:4]), int(row["month"][5:7])
        f.write(f"{y + (m - 0.5) / 12:.3f},{float(row['cor1m']):.2f}\n")

m = monthly()
cv, cc = np.cumsum(m["vega"] / m["vega"].std()), np.cumsum(m["corrswap"] / m["corrswap"].std())
with open(OUT / "books.csv", "w") as f:
    f.write("year,vega,corrswap\n")
    for i, s in enumerate(m["start"]):
        f.write(f"{(s + TENOR) / 252:.3f},{cv[i]:.3f},{cc[i]:.3f}\n")
