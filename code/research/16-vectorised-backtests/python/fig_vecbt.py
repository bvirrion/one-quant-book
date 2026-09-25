"""Chart data for Book 7, chapter 16 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_vecbt import waterfall  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

rev, mom = waterfall("reversal"), waterfall("momentum")
with open(OUT / "waterfall.csv", "w") as f:
    f.write("k,reversal,momentum\n")
    for k, (a, b) in enumerate(zip(rev, mom, strict=True)):
        f.write(f"{k},{a[1]:.4f},{b[1]:.4f}\n")

paths = {"gross": rev[2][4], "costed": rev[4][4], "next": rev[5][4], "momentum": mom[5][4]}
with open(OUT / "capital.csv", "w") as f:
    f.write("year," + ",".join(paths) + "\n")
    for t in range(0, len(rev[0][4].net), 5):
        logs = (f"{np.log10(max(p.capital[t], 1e-300)):.4f}" for p in paths.values())
        f.write(f"{t / 252:.3f}," + ",".join(logs) + "\n")
