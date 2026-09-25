"""Chart data for Book 9, chapter 16 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_sysmacro import START, YEAR, books, stats  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

_, _, b = books()
keys = ("value", "momentum", "carry", "surprise", "combined")
cum = {k: np.cumsum(b[k][START:]) for k in keys}
with open(OUT / "cumulative.csv", "w") as f:
    f.write("year," + ",".join(keys) + "\n")
    for i in range(0, len(cum["value"]), 5):
        f.write(f"{i / YEAR:.3f}," + ",".join(f"{100 * cum[k][i]:.2f}" for k in keys) + "\n")

s = stats()
with open(OUT / "sharpe.csv", "w") as f:
    f.write("x,label,sr\n")
    for i, k in enumerate(("value", "reversal", "momentum", "carry", "surprise", "combined", "combined, price value",
                           "combined, no value")):
        f.write(f"{i + 1},{k.replace(', ', ' ')},{s[k]['sr']:.2f}\n")
