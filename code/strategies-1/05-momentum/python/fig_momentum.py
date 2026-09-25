"""Chart data for Book 8, chapter 5 (deterministic)."""
import csv
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_momentum import DATA, START, YEAR, book  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(DATA / "mom_annual.csv") as f, open(OUT / "annual.csv", "w") as g:
    g.write("year,raw_pct,scaled_pct\n")
    for row in csv.DictReader(f):
        if int(row["year"]) >= 1928 and int(row["year"]) <= 2025:
            g.write(f"{row['year']},{100 * float(row['raw']):.2f},{100 * float(row['scaled']):.2f}\n")

cum = {k: np.cumsum(book(k)["net"]) for k in ("total", "residual", "industry")}
with open(OUT / "books.csv", "w") as f:
    f.write("year,total,residual,industry\n")
    for i in range(0, len(cum["total"]), 5):
        f.write(f"{(START + i) / YEAR:.3f}," + ",".join(f"{100 * cum[k][i]:.3f}" for k in cum) + "\n")
