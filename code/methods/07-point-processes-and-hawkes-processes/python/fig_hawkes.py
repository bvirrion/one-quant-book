"""Chart data for Book 4, Chapter 7 (deterministic, seeded)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_hawkes import ALPHA, BETA, DAY, MU, dispersion_sim, dispersion_theory, fit, residuals, simulate_thinning

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

t = simulate_thinning(MU, ALPHA, BETA, DAY, seed=1)
w0, w1 = 3600.0, 3660.0                        # one minute, an hour after the open
ev = t[(t >= w0) & (t <= w1)]
grid = np.sort(np.concatenate([np.linspace(w0, w1, 1201), ev, ev - 1e-6]))
lam = np.full(grid.size, MU)
for ti in t[(t < w1) & (t > w0 - 40)]:
    m = grid > ti
    lam[m] += ALPHA * np.exp(-BETA * (grid[m] - ti))
with open(OUT / "intensity.csv", "w") as f:
    f.write("s,lam\n")
    for g, v in zip(grid, lam, strict=True):
        f.write(f"{g - w0:.6f},{v:.5f}\n")
with open(OUT / "events.csv", "w") as f:
    f.write("s,y\n")
    for e in ev:
        f.write(f"{e - w0:.4f},-0.15\n")

with open(OUT / "dispersion.csv", "w") as f:
    f.write("tau,theory,sim\n")
    for tau in (0.25, 0.5, 1, 2, 5, 10, 20, 60, 120, 300):
        f.write(f"{tau},{dispersion_theory(tau):.4f},{dispersion_sim(t, tau):.4f}\n")

fh = fit(t, DAY)
r_h = np.sort(residuals(t, fh["mu"], fh["alpha"], fh["beta"]))
r_p = np.sort(np.diff(np.concatenate([[0.0], t])) * (t.size / DAY))
n = r_h.size
with open(OUT / "qq.csv", "w") as f:
    f.write("q,hawkes,poisson\n")
    for k in np.unique(np.round(np.geomspace(1, n, 120)).astype(int)):
        p = (k - 0.5) / n
        f.write(f"{-math.log(1 - p):.4f},{r_h[k - 1]:.4f},{r_p[k - 1]:.4f}\n")
