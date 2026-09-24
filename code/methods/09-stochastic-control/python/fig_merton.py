"""Chart data for Book 4, Chapter 9 (deterministic, seeded)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_merton import MU, SIGMA, R, ce_rate, dp_merton, merton_fraction, viscosity_profile

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "ce.csv", "w") as f:
    f.write("pi,ce\n")
    for pi in np.linspace(0, 1.6, 81):
        f.write(f"{pi:.3f},{100 * ce_rate(pi):.5f}\n")

dp = dp_merton()
with open(OUT / "policy.csv", "w") as f:
    f.write("wealth,pi\n")
    for x, p in zip(dp["grid"][dp["inner"]], dp["policy0"][dp["inner"]], strict=True):
        f.write(f"{math.exp(x):.4f},{p:.4f}\n")

with open(OUT / "sensitivity.csv", "w") as f:
    f.write("excess,g2,g3,g5\n")
    for ex in np.linspace(0.0, 0.10, 41):
        f.write(f"{100 * ex:.2f}," + ",".join(f"{merton_fraction(mu=R + ex, gamma=g):.4f}" for g in (2, 3, 5)) + "\n")

rng = np.random.default_rng(5)
n = 20_000
stock, cash = np.full(n, 0.6), np.full(n, 0.4)
with open(OUT / "drift.csv", "w") as f:
    f.write("year,p10,p50,p90\n")
    f.write("0,0.6,0.6,0.6\n")
    for day in range(1, 10 * 252 + 1):
        g = np.exp((MU - 0.5 * SIGMA**2) / 252 + SIGMA / math.sqrt(252) * rng.standard_normal(n))
        stock *= g
        cash *= 1 + R / 252
        if day % 21 == 0:
            w = stock / (stock + cash)
            f.write(f"{day / 252:.3f},{np.quantile(w, 0.1):.4f},{np.median(w):.4f},{np.quantile(w, 0.9):.4f}\n")

with open(OUT / "viscosity.csv", "w") as f:
    f.write("x,e02,e005,e0\n")
    for x in np.linspace(-1, 1, 201):
        f.write(f"{x:.3f},{viscosity_profile(0.2, x):.5f},{viscosity_profile(0.05, x):.5f},{1 - abs(x):.5f}\n")
