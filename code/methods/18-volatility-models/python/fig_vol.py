"""Chart data for Book 4, Chapter 18 (ECB reference rates in data/methods; simulations seeded)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_vol import WINDOW, evaluate, ewma, garch_fit, ghost, impulse, load, rolling_var, rv_convergence

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

d = load()
r, dates = d["r"], d["dates"]
g = ghost()
j = g["index"]
f = garch_fit(r, "t")
vol_g, vol_e, vol_w = np.sqrt(f["h"]), np.sqrt(ewma(r)), np.sqrt(rolling_var(r, WINDOW))
with open(OUT / "ghost.csv", "w") as fh:
    fh.write("k,window,garch,ewma,absr\n")
    for t in range(j - 300, min(j + 60, r.size)):
        fh.write(f"{t - j},{vol_w[t]:.4f},{vol_g[t]:.4f},{vol_e[t]:.4f},{abs(r[t]):.4f}\n")

with open(OUT / "history.csv", "w") as fh:
    fh.write("year,absr,garch\n")
    for t in range(0, r.size, 5):
        y, m, dd = (int(v) for v in dates[t].split("-"))
        fh.write(f"{y + (m - 1) / 12 + (dd - 1) / 365:.4f},{abs(r[t]):.4f},{vol_g[t]:.4f}\n")

imp = impulse()
with open(OUT / "impulse.csv", "w") as fh:
    fh.write("day,garch,ewma,window\n")
    for i, k in enumerate(imp["k"]):
        fh.write(f"{k},{imp['garch'][i]:.5f},{imp['ewma'][i]:.5f},{imp['window'][i]:.5f}\n")

rc = rv_convergence()
with open(OUT / "rv.csv", "w") as fh:
    fh.write("m,error,theory\n")
    for m, e in rc:
        fh.write(f"{m},{e:.4f},{math.sqrt(2 / m):.4f}\n")

E = evaluate()
with open(OUT / "eval.csv", "w") as fh:
    fh.write("k,model,qlike\n")
    for k, name in enumerate(("garch", "ewma", "window")):
        fh.write(f"{k},{name},{E[name]['qlike'] - E['window']['qlike']:.4f}\n")
