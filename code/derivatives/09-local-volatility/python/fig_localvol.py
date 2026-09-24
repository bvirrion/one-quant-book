"""Chart data for Book 5, Chapter 9 (deterministic)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_localvol import dynamics, forward_smile, implied, local, mc_smile

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "local_vs_implied.csv", "w") as f:
    f.write("k,imp3m,loc3m,imp1y,loc1y\n")
    for k in np.arange(-0.40, 0.3001, 0.01):
        f.write(f"{k:.2f},{100 * implied(k, 0.25):.4f},{100 * local(k, 0.25):.4f},"
                f"{100 * implied(k, 1.0):.4f},{100 * local(k, 1.0):.4f}\n")

with open(OUT / "reprice.csv", "w") as f:
    f.write("strike,mc,lo,hi\n")
    for r in mc_smile(strikes=(75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125)):
        f.write(f"{r['strike']},{100 * r['mc_vol']:.4f},{100 * (r['mc_vol'] - 2 * r['se_vol']):.4f},"
                f"{100 * (r['mc_vol'] + 2 * r['se_vol']):.4f}\n")
with open(OUT / "surface6m.csv", "w") as f:
    f.write("strike,vol\n")
    for k in range(72, 129):
        f.write(f"{k},{100 * implied(math.log(k / 100), 0.5):.4f}\n")

with open(OUT / "forward_smile.csv", "w") as f:
    f.write("x,forward,today\n")
    for x, fv, tv in forward_smile():
        f.write(f"{x:.3f},{100 * fv:.4f},{100 * tv:.4f}\n")

strikes = tuple(range(85, 116, 5))
d = dynamics(strikes=strikes)
with open(OUT / "dynamics.csv", "w") as f:
    f.write("strike,before,after_lv,after_delta\n")
    for k, b, a in zip(strikes, d["before"], d["after"], strict=True):
        sd = 100 * implied(math.log(k / 95.0), 0.25)            # sticky delta: today's smile around the new spot
        f.write(f"{k},{100 * b:.4f},{100 * a:.4f},{sd:.4f}\n")
