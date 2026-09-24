"""Chart data for Book 3, Chapter 12 (deterministic: fixed seeds)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_options import F0, SIGMA, T, averages, sovereign

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/hedgeprog"))
from firm_hedgeprog import Leg, hedged_revenue, three_way, value

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

avg = averages()
put = value([Leg("put", 55.0)], avg, 0.04, 1.0)
k3 = sovereign()["call_strike"]
x = np.linspace(20, 110, 91)
with open(OUT / "payoffs.csv", "w") as f:
    f.write("x,unhedged,collar,threeway,put\n")
    c = hedged_revenue(x, [Leg("put", 50.0), Leg("call", 75.0, -1)], 0.0)
    tw = hedged_revenue(x, three_way(60.0, 45.0, k3), 0.0)
    p = hedged_revenue(x, [Leg("put", 55.0)], put)
    for row in zip(x, x, c, tw, p, strict=True):
        f.write(",".join(f"{v:.3f}" for v in row) + "\n")
rng = np.random.default_rng(11)
term = F0 * np.exp(-0.5 * SIGMA ** 2 * T + SIGMA * np.sqrt(T) * rng.standard_normal(len(avg)))
edges = np.arange(10, 151, 5)
ht, _ = np.histogram(term, bins=edges)
ha, _ = np.histogram(avg, bins=edges)
with open(OUT / "dist.csv", "w") as f:
    f.write("mid,terminal,average\n")
    for m, a, b in zip((edges[:-1] + edges[1:]) / 2, ht, ha, strict=True):
        f.write(f"{m:.1f},{100 * a / len(term):.3f},{100 * b / len(avg):.3f}\n")

q = np.linspace(0.005, 0.995, 199)
unh = avg
col = hedged_revenue(avg, [Leg("put", 50.0), Leg("call", 75.0, -1)], 0.0)
pp = hedged_revenue(avg, [Leg("put", 55.0)], put)
with open(OUT / "revcdf.csv", "w") as f:
    f.write("p,unhedged,collar,put\n")
    for row in zip(q, np.quantile(unh, q), np.quantile(col, q), np.quantile(pp, q), strict=True):
        f.write(",".join(f"{v:.3f}" for v in row) + "\n")
