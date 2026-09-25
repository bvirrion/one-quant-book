"""Chart data for Book 8, chapter 12 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_structrv import fund  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

a, b = fund(0.0), fund(0.3)
edges = np.arange(0.0, 3.01, 0.25)
with open(OUT / "exit.csv", "w") as f:
    f.write("years,no_catalyst,catalyst\n")
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        n1 = ((a["years"] > lo) & (a["years"] <= hi)).mean()
        n2 = ((b["years"] > lo) & (b["years"] <= hi)).mean()
        f.write(f"{(lo + hi) / 2:.3f},{100 * n1:.2f},{100 * n2:.2f}\n")
