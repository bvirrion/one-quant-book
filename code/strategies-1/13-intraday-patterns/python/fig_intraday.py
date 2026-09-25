"""Chart data for Book 8, chapter 13 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_intraday import days, smile  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "smile.csv", "w") as f:
    f.write("bar,share_pct\n")
    for k, w in enumerate(smile()):
        f.write(f"{k + 1},{100 * w:.3f}\n")

rows = {}
for g in (0.0, 0.05):
    d = days(g)
    rest = d["overnight"] + d["bars"][:, :-1].sum(axis=1)
    last = d["bars"][:, -1]
    edges = np.quantile(rest, np.linspace(0, 1, 11))
    k = np.clip(np.searchsorted(edges, rest, side="right") - 1, 0, 9)
    rows[g] = [(100 * rest[k == i].mean(), 1e4 * last[k == i].mean()) for i in range(10)]
with open(OUT / "binned.csv", "w") as f:
    f.write("rest0,last0_bp,rest5,last5_bp\n")
    for a, b in zip(rows[0.0], rows[0.05], strict=True):
        f.write(f"{a[0]:.3f},{a[1]:.3f},{b[0]:.3f},{b[1]:.3f}\n")
