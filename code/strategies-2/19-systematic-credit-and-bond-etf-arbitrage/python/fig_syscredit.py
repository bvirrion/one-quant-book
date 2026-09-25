"""Chart data for Book 9, chapter 19 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_syscredit import FACTORS, START, YEAR, market  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

cfg, sim, books = market()
a, b = sim["stress"]
base = sim["basket"][a - 1]
with open(OUT / "etf.csv", "w") as f:
    f.write("day,true,nav,price\n")
    for t in range(a - 10, b + cfg.stress_back + 10):
        f.write(f"{t - a},{100 * sim['basket'][t] / base:.3f},{100 * sim['nav'][t] / base:.3f},"
                f"{100 * sim['price'][t] / base:.3f}\n")

keys = FACTORS + ("combined",)
cum = {k: np.cumsum(books[k][START:] / books[k][START:].std() * 0.1 / np.sqrt(YEAR)) for k in keys}
with open(OUT / "factors.csv", "w") as f:
    f.write("year," + ",".join(keys) + "\n")
    for i in range(0, len(cum["value"]), 5):
        f.write(f"{i / YEAR:.3f}," + ",".join(f"{100 * cum[k][i]:.2f}" for k in keys) + "\n")
