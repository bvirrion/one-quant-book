"""Chart data for Book 3, Chapter 1 (deterministic: fixed seeds, data/markets-3)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_physical import back_to_back, load_differential, simulate_cargo

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "differential.csv", "w") as f:
    f.write("t,spread\n")
    for m, w, b in load_differential():
        f.write(f"{int(m[:4]) + (int(m[5:]) - 0.5) / 12:.4f},{w - b:.2f}\n")

bb = back_to_back()
held = 0
with open(OUT / "exposure.csv", "w") as f:
    f.write("day,exposure,hedge\n")
    for d, e in bb["profile"]:
        held += bb["trades"].get(d, 0)
        f.write(f"{d},{e / 1000:.0f},{held}\n")

s = simulate_cargo()
q = np.linspace(0.005, 0.995, 199)
with open(OUT / "costcdf.csv", "w") as f:
    f.write("p,unhedged,hedged\n")
    for p, u, h in zip(q, np.quantile(s["unhedged"], q), np.quantile(s["hedged"], q), strict=True):
        f.write(f"{p:.3f},{u:.3f},{h:.3f}\n")
