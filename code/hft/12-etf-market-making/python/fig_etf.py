"""Chart data for Book 11, chapter 12 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hf_etf as h  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

s = h.SEEDS[0]
mk = h.market(s)
mm = h.run("basket, hedged", s)["mid"]
a, b = 37 * h.fe.MINUTES, 50 * h.fe.MINUTES
base = mk.true[a] / 100.0
with open(OUT / "freeze.csv", "w") as f:
    f.write("day,true,nav,mm\n")
    for t in range(a, b, 10):
        f.write(f"{t / h.fe.MINUTES:.3f},{mk.true[t] / base:.3f},{mk.nav[t] / base:.3f},{mm[t] / base:.3f}\n")

with open(OUT / "cumulative.csv", "w") as f:
    f.write("day,nav,basket\n")
    cn = np.cumsum(h.run("NAV, hedged", s)["total"]) / 1e6
    cb = np.cumsum(h.run("basket, hedged", s)["total"]) / 1e6
    for d in range(mk.days):
        f.write(f"{d + 1},{cn[d]:.3f},{cb[d]:.3f}\n")
