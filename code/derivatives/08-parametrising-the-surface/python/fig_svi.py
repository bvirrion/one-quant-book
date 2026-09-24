"""Chart data for Book 5, Chapter 8 (deterministic)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_svi import KS, T3, earnings_vols, fit_slice, quotes, spline_through_mids, ssvi, ssvi_fit, svi

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

r = fit_slice()
with open(OUT / "quotes.csv", "w") as f:
    f.write("k,bid,mid,ask\n")
    for k, b, m, a in zip(KS, r["bid"], r["mid"], r["ask"], strict=True):
        f.write(f"{k:.4f},{100 * b:.4f},{100 * m:.4f},{100 * a:.4f}\n")
grid, spl = spline_through_mids(grid=np.linspace(-0.40, 0.25, 261))
with open(OUT / "fits.csv", "w") as f:
    f.write("k,svi,spline\n")
    for g, sp in zip(grid, spl, strict=True):
        f.write(f"{g:.4f},{100 * math.sqrt(float(svi(g, *r['params'])) / T3):.4f},{100 * sp:.4f}\n")

s = ssvi_fit()
rho, eta, gam = s["params"]
with open(OUT / "ssvi.csv", "w") as f:
    f.write("k,m1,m1fit,m3,m3fit,y1,y1fit\n")
    mids = {d: quotes(d / 365, seed=d)[1] for d in (30, 91, 365)}
    for i, k in enumerate(KS):
        row = []
        for d, th in ((30, s["thetas"][0]), (91, s["thetas"][1]), (365, s["thetas"][3])):
            t = d / 365
            row += [100 * mids[d][i], 100 * math.sqrt(float(ssvi(k, th, rho, eta, gam)) / t)]
        f.write(f"{k:.4f}," + ",".join(f"{x:.4f}" for x in row) + "\n")

with open(OUT / "wings.csv", "w") as f:
    f.write("k,w,lee\n")
    for k in np.linspace(-2.0, 2.0, 81):
        f.write(f"{k:.3f},{float(svi(k, *r['params'])):.5f},{2 * abs(k):.5f}\n")

with open(OUT / "earnings.csv", "w") as f:
    f.write("days,vol,base\n")
    for d, v in earnings_vols():
        f.write(f"{d},{100 * v:.3f},32\n")
