"""Chart data for Book 4, Chapter 10 (deterministic, seeded)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_bands import (
    GAMMA,
    SIGMA,
    K,
    cost_curve,
    daily_hedge_cost,
    dp_stopping_check,
    optimal_fixed_band,
    optimal_proportional_band,
)

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

b_star, _ = optimal_fixed_band(SIGMA, GAMMA, K)
rng = np.random.default_rng(4)
steps = 390 * 10
x, rows = 0.0, []
for k in range(steps + 1):
    rows.append((k / 390, x))
    x += SIGMA * math.sqrt(1 / 390) * rng.standard_normal()
    if abs(x) >= b_star:
        rows.append(((k + 1) / 390, math.copysign(b_star, x)))
        x = 0.0
with open(OUT / "exposure.csv", "w") as f:
    f.write("day,x\n")
    for d, v in rows:
        f.write(f"{d:.5f},{v:.4f}\n")

with open(OUT / "cost.csv", "w") as f:
    f.write("b,cost,daily\n")
    for b, cst in cost_curve():
        f.write(f"{b:.2f},{cst:.3f},{daily_hedge_cost():.1f}\n")

with open(OUT / "laws.csv", "w") as f:
    f.write("scale,b_fixed,b_prop\n")
    for s in np.geomspace(0.1, 10, 21):
        bf = optimal_fixed_band(SIGMA, GAMMA, K * s)[0]
        bp = optimal_proportional_band(SIGMA, GAMMA, 25.0 * s)[0]
        f.write(f"{s:.4f},{bf:.4f},{bp:.4f}\n")

chk = dp_stopping_check()
b, th = chk["b_star"], chk["theta"]
with open(OUT / "stopping.csv", "w") as f:
    f.write("x,value,payoff\n")
    for xx in np.linspace(-10, 60, 141):
        v = (b - 5.0) * math.exp(th * (xx - b)) if xx < b else xx - 5.0
        f.write(f"{xx:.2f},{v:.4f},{max(xx - 5.0, 0.0):.4f}\n")
