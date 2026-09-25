"""Chart data for Book 9, chapter 18 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_creditrv import YEAR, market, negative_basis  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

cfg, s = market()
b = s["basis"].mean(axis=1)
c0 = np.cumsum(negative_basis(s, cfg, 0.0)["on_capital"])
c30 = np.cumsum(negative_basis(s, cfg, 30.0)["on_capital"])
with open(OUT / "basis.csv", "w") as f:
    f.write("year,basis,book0,book30\n")
    for t in range(0, len(c0), 5):
        f.write(f"{(t + 1) / YEAR:.3f},{b[t + 1]:.2f},{100 * c0[t]:.2f},{100 * c30[t]:.2f}\n")
