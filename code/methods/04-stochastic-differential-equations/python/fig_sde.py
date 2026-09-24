"""Chart data for Book 4, Chapter 4 (deterministic, seeded)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_sde import DESK, feller_table, ou_exact, sqrt_exact, stationary_histograms

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

ou = ou_exact(0.5, 2.0, 0.0, 0.2, 1.0, 252, 3, seed=2)
sq = sqrt_exact(DESK["v0"], DESK["kappa"], DESK["vbar"], DESK["eta"], 1.0, 252, 3, seed=3)
t = np.linspace(0, 1, 253)
with open(OUT / "paths.csv", "w") as f:
    f.write("t,ou0,ou1,ou2,ou_mean,v0,v1,v2\n")
    for k in range(253):
        mean = 0.5 * np.exp(-2.0 * t[k])
        f.write(f"{t[k]:.4f}," + ",".join(f"{x:.5f}" for x in ou[:, k]) + f",{mean:.5f},"
                + ",".join(f"{x:.5f}" for x in sq[:, k]) + "\n")

with open(OUT / "feller.csv", "w") as f:
    f.write("ratio,daily,fine\n")
    for r, d, fine in feller_table():
        f.write(f"{r:.4f},{d:.4f},{fine:.4f}\n")

h = stationary_histograms()
with open(OUT / "stationary.csv", "w") as f:
    f.write("v,desk_hist,desk_pdf,f2_hist,f2_pdf\n")
    for i in range(h["desk"][0].size):
        f.write(f"{h['desk'][0][i]:.4f},{h['desk'][1][i]:.4f},{h['desk'][2][i]:.4f},"
                f"{h['feller2'][1][i]:.4f},{h['feller2'][2][i]:.4f}\n")
