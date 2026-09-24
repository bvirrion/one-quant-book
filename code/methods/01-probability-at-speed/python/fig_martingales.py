"""Chart data for Book 4, Chapter 1 (deterministic, seeded)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_martingales import MINUTES, NEWS, T_IMB, close_paths, close_variances, stop_table

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

# one simulated day of the closing-price forecast; the news column sits at minute 380 as well
day = close_paths(1, seed=11)[0]
minutes = list(range(T_IMB + 1)) + [T_IMB] + list(range(T_IMB + 1, MINUTES + 1))
with open(OUT / "day.csv", "w") as f:
    f.write("minute,forecast\n")
    for m, x in zip(minutes, day, strict=True):
        f.write(f"{m},{x:.4f}\n")

# share of the close's variance resolved by each time of day: theory and 20,000 simulated days
v = close_variances()
paths = close_paths(20_000, seed=12)
var_close = paths[:, -1].var()
with open(OUT / "resolved.csv", "w") as f:
    f.write("minute,theory,sim\n")
    checkpoints = list(range(0, T_IMB + 1, 20))
    for m in checkpoints:
        col = m
        th = v["per_min"][:m].sum() / v["total"]
        sim = np.var(paths[:, col] - paths[:, 0]) / var_close
        f.write(f"{m},{th:.5f},{sim:.5f}\n")
    th = (v["per_min"][:T_IMB].sum() + 0.3**2) / v["total"]
    f.write(f"{T_IMB},{th:.5f},{np.var(paths[:, NEWS] - paths[:, 0]) / var_close:.5f}\n")
    f.write(f"{MINUTES},1.00000,{1.0:.5f}\n")

with open(OUT / "stops.csv", "w") as f:
    f.write("b,fair_theory,fair_sim,drift_theory,drift_sim\n")
    for row in stop_table():
        f.write(",".join([str(row[0])] + [f"{x:.4f}" for x in row[1:]]) + "\n")
