"""Chart data for Book 16, chapter 9 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_research as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

c = m.credit()
with open(OUT / "credit.csv", "w") as f:
    f.write("k,name,alone,loo,shapley,order_abc\n")
    for i, nm in enumerate(m.NAMES):
        f.write(f"{i},{nm},{c['alone'][i]:.2f},{c['loo'][i]:.2f},{c['shapley'][i]:.2f},{c['orders']['ABC'][i]:.2f}\n")

g, r = m.portfolio_samples()
edges = np.arange(-12.0, 40.1, 4.0)
hg, _ = np.histogram(g, edges)
hr, _ = np.histogram(r, edges)
with open(OUT / "portfolio.csv", "w") as f:
    f.write("centre,greedy,random\n")
    for lo, a, b in zip(edges[:-1], hg, hr, strict=True):
        f.write(f"{lo + 2.0:.1f},{100 * a / len(g):.2f},{100 * b / len(r):.2f}\n")

with open(OUT / "dsr.csv", "w") as f:
    f.write("trials,dsr\n")
    for t, d in m.dsr_curve():
        f.write(f"{t},{d:.4f}\n")
