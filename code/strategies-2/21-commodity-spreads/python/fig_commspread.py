"""Chart data for Book 9, chapter 21 (deterministic)."""
import csv
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_commspread import DATA, YEAR, market  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(DATA / "spreads_monthly.csv") as fh, open(OUT / "real.csv", "w") as f:
    f.write("year,crack,brentwti\n")
    for r in csv.DictReader(fh):
        y, m = int(r["month"][:4]), int(r["month"][5:])
        f.write(f"{y + (m - 0.5) / 12:.3f},{float(r['crack321']):.2f},{float(r['brentwti']):.2f}\n")

_, s, books = market()
cum = {k: np.cumsum(books[k]) for k in ("crack", "seasonal", "location", "quality")}
with open(OUT / "books.csv", "w") as f:
    f.write("year,crack,seasonal,location,quality\n")
    for t in range(YEAR, len(s["crude"]), 5):
        f.write(f"{t / YEAR:.3f}," + ",".join(f"{cum[k][t]:.2f}" for k in cum) + "\n")
