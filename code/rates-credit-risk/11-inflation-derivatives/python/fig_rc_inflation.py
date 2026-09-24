"""Chart data for Book 6, chapter 11 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rc_inflation import convexity_table, model, seasonal_forward_path  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "convexity.csv", "w") as f:
    f.write("i,fwd,yoy,adj\n")
    for i, a, b, c in convexity_table():
        f.write(f"{i},{a:.4f},{b:.4f},{c:.3f}\n")
with open(OUT / "seasonal.csv", "w") as f:
    f.write("m,smooth,seasonal\n")
    for k, a, b in seasonal_forward_path():
        f.write(f"{k},{a:.4f},{b:.4f}\n")

r = model().simulate_ratios(20, 40000)
lpi = np.prod(1 + np.clip(r - 1, 0.0, 0.05), axis=1)
full = np.prod(r, axis=1)
edges = np.arange(0.9, 3.21, 0.05)
h1, _ = np.histogram(lpi, edges)
h2, _ = np.histogram(full, edges)
with open(OUT / "lpihist.csv", "w") as f:
    f.write("x,lpi,full\n")
    for a, b, c in zip(edges[:-1], h1, h2, strict=True):
        f.write(f"{a + 0.025:.3f},{100 * b / len(lpi):.3f},{100 * c / len(full):.3f}\n")
