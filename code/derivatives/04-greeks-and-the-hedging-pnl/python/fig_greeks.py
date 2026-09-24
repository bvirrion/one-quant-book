"""Chart data for Book 5, Chapter 4 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_greeks import gamma_path, greeks, hedge_short_straddle

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "shapes.csv", "w") as f:
    f.write("spot,g1,g025,g005,v1,v025,v005\n")
    for s in range(70, 131):
        gs = [greeks(s, 100, t, 0.0, 0.0, 0.2, "C") for t in (1.0, 0.25, 0.05)]
        f.write(f"{s}," + ",".join(f"{g['gamma']:.5f}" for g in gs) + ","
                + ",".join(f"{0.01 * g['vega']:.5f}" for g in gs) + "\n")

days, pnl, pred = gamma_path()
with open(OUT / "gamma_path.csv", "w") as f:
    f.write("day,pnl,pred\n")
    for d, a, b in zip(days, pnl, pred, strict=True):
        f.write(f"{d:.2f},{a:.4f},{b:.4f}\n")


def hist(x, edges):
    counts, _ = np.histogram(x, bins=edges)
    return counts / (len(x) * (edges[1] - edges[0]))


edges = np.arange(-4.05, 4.06, 0.1)
centres = 0.5 * (edges[1:] + edges[:-1])
daily = hedge_short_straddle(20_000, 21, vol_real=0.20, seed=4)
hourly = hedge_short_straddle(20_000, 168, vol_real=0.20, seed=4)
with open(OUT / "discrete.csv", "w") as f:
    f.write("x,daily,eight\n")
    for c, a, b in zip(centres, hist(daily, edges), hist(hourly, edges), strict=True):
        f.write(f"{c:.2f},{a:.4f},{b:.4f}\n")

edges = np.arange(-5.05, 3.06, 0.1)
centres = 0.5 * (edges[1:] + edges[:-1])
at_imp = hedge_short_straddle(20_000, 84, seed=6)
at_real = hedge_short_straddle(20_000, 84, hedge_vol=0.25, seed=6)
with open(OUT / "which_vol.csv", "w") as f:
    f.write("x,implied,realised\n")
    for c, a, b in zip(centres, hist(at_imp, edges), hist(at_real, edges), strict=True):
        f.write(f"{c:.2f},{a:.4f},{b:.4f}\n")
