"""Chart data for Book 8, chapter 17 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_news import capture  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "latency.csv", "w") as f:
    f.write("latency,share_pct\n")
    for lat in np.logspace(-3, 2, 26):
        f.write(f"{lat:.6f},{100 * capture(lat)[0]:.3f}\n")
