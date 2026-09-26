"""Chart data for Book 10, chapter 14 (deterministic)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_ac import ETA, SIGMA, X, block_study, sim_study  # noqa: E402, I001
from firm_acexec import frontier, kappa, trajectory  # noqa: E402, I001

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

t = np.linspace(0, 1, 27)
with open(OUT / "trajectories.csv", "w") as f:
    f.write("hours," + ",".join(f"k{i}" for i in range(4)) + "\n")
    ks = [0.0, 1.0, kappa(ETA, SIGMA, 1e-6), 8.0]
    for x in t:
        f.write(f"{6.5 * x:.3f}," + ",".join(f"{trajectory(1.0, 1.0, k, x):.5f}" for k in ks) + "\n")
lams = np.exp(np.linspace(np.log(1e-9), np.log(1e-4), 30))
with open(OUT / "frontier.csv", "w") as f:
    f.write("sd,cost\n")
    for e, v in frontier(X, 1.0, 390, 0.0, ETA, SIGMA, lams):
        f.write(f"{math.sqrt(v) / 1000:.3f},{e / 1000:.3f}\n")
b = block_study()
with open(OUT / "points.csv", "w") as f:
    f.write("name,sd,cost\n")
    f.write(f"optimal,{b['sd'] / 1000:.3f},{b['cost'] / 1000:.3f}\n")
    for k in ("twap", "patient", "hurried"):
        f.write(f"{k},{b[k][1] / 1000:.3f},{b[k][0] / 1000:.3f}\n")
s = sim_study()
with open(OUT / "sim.csv", "w") as f:
    f.write("kt,mean,se,sd,model_mean,model_sd\n")
    for kt in (0.0, 2.0, 6.0):
        v = s[kt]
        f.write(f"{kt},{v['mean']:.4f},{v['se']:.4f},{v['sd']:.4f},{v['model_mean']:.4f},{v['model_sd']:.4f}\n")
