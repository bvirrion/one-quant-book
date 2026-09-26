"""Chart data for Book 12, chapter 1 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ml_why import compare, drift_by_year, learning_curve  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/ml" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

c = compare()
with open(OUT / "learning.csv", "w") as f:
    f.write("months,boosting,ridge,ceiling\n")
    for m, g, r in learning_curve():
        f.write(f"{m},{100 * g:.4f},{100 * r:.4f},{100 * c['ceiling_oos']:.4f}\n")

rows = drift_by_year()
with open(OUT / "drift.csv", "w") as f:
    f.write("year,stationary,changing,ceiling_changing\n")
    st = {y: v for d, y, v, _ in rows if not d}
    for d, y, v, cl in rows:
        if d:
            f.write(f"{y},{100 * st[y]:.4f},{100 * v:.4f},{100 * cl:.4f}\n")

edges = np.arange(-1.0, 2.76, 0.25)                     # per cent; zero is an edge: bars left of it are losing months
with open(OUT / "months.csv", "w") as f:
    f.write("x,boosting,truth\n")
    hb, _ = np.histogram(100 * c["months_oos"]["boosting"], edges)
    ht, _ = np.histogram(100 * c["months_truth"], edges)
    for x, a, b in zip(0.5 * (edges[:-1] + edges[1:]), hb, ht, strict=True):
        f.write(f"{x:.3f},{a},{b}\n")
