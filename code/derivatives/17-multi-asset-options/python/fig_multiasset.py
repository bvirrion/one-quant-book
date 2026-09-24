"""Chart data for Book 5, Chapter 17 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_multiasset import (
    INDEX_STRIKES,
    calibrate_local_correlation,
    correlation_by_strike,
    dispersion,
    index_vol,
    quanto_example,
    three_share_prices,
)

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "three_share.csv", "w") as f:
    f.write("rho,worst_digital,worst_put,best_call,basket_call\n")
    for r in three_share_prices():
        f.write(f"{r['rho']:.2f},{r['worst_digital']:.5f},{r['worst_put']:.5f},{r['best_call']:.5f},"
                f"{r['basket_call']:.5f}\n")

rc = correlation_by_strike()
lc = calibrate_local_correlation()
with open(OUT / "corr_skew.csv", "w") as f:
    f.write("k,index_vol,implied_corr,lc_vol,const_vol\n")
    for i, k in enumerate(INDEX_STRIKES):
        f.write(f"{k:.0f},{100 * index_vol(k):.4f},{rc[k]:.5f},"
                f"{100 * lc['fitted'][i]:.4f},{100 * lc['constant'][i]:.4f}\n")
with open(OUT / "local_corr.csv", "w") as f:
    f.write("x,rho\n")
    for x in np.linspace(-0.25, 0.25, 51):
        f.write(f"{x:.3f},{float(np.clip(lc['a'] - lc['b'] * x + lc['c'] * x * x, 0.0, 0.999)):.5f}\n")

d = dispersion()
edges = np.linspace(100.0, 450.0, 36)
h = np.histogram(d["pnl"] / 1e3, edges)[0] / len(d["pnl"])
with open(OUT / "dispersion.csv", "w") as f:
    f.write("pnl,share\n")
    for i in range(len(h)):
        f.write(f"{edges[i]:.1f},{h[i]:.5f}\n")
    f.write(f"{edges[-1]:.1f},{h[-1]:.5f}\n")

with open(OUT / "quanto.csv", "w") as f:
    f.write("rho,analytic,mc\n")
    for r in quanto_example():
        f.write(f"{r['rho']:.2f},{r['analytic']:.4f},{r['mc']:.4f}\n")
