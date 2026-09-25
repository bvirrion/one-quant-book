"""Chart data for Book 8, chapter 2 (deterministic)."""
import csv
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_reversal import START, YEAR, traded  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
DATA = HERE.parents[4] / "data" / "strategies-1"
CURVE = (1e8, 3e8, 1e9, 3e9, 1e10)

with open(DATA / "strev_rolling.csv") as f, open(OUT / "rolling.csv", "w") as g:
    g.write("year,mean_pct\n")
    for row in csv.DictReader(f):
        g.write(f"{row['year']},{100 * float(row['mean']):.3f}\n")

with open(OUT / "size.csv", "w") as f:
    f.write("log10_aum,sr_gross,sr_net\n")
    for a in CURVE:
        r = traded(a, True, 1.0, True)
        f.write(f"{np.log10(a):.3f},{r['sr_gross']:.4f},{r['sr_net']:.4f}\n")

a, b = traded(1e9, True, 1.0, True)["net"], traded(1e9, True, 1.0, False)["net"]
ca, cb = np.cumsum(a), np.cumsum(b)
with open(OUT / "earnings.csv", "w") as f:
    f.write("year,filtered_pct,unfiltered_pct\n")
    for i in range(0, len(a), 5):
        f.write(f"{(START + i) / YEAR:.3f},{100 * ca[i]:.4f},{100 * cb[i]:.4f}\n")
