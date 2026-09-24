"""Chart data for Book 5, Chapter 3 (deterministic)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_blackscholes import CASE, bs, replicate_path

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
c = CASE

with open(OUT / "call_vs_spot.csv", "w") as f:
    f.write("spot,t1,t05,t01,payoff\n")
    for s in range(60, 141, 2):
        v = [bs(s, c["strike"], t, c["r"], c["q"], c["vol"], "C") for t in (1.0, 0.5, 0.1)]
        f.write(f"{s},{v[0]:.4f},{v[1]:.4f},{v[2]:.4f},{max(s - c['strike'], 0.0):.4f}\n")

t, s, opt, port = replicate_path()
with open(OUT / "replication.csv", "w") as f:
    f.write("t,spot,option,portfolio\n")
    for i in range(0, len(t), 2):
        f.write(f"{t[i]:.4f},{s[i]:.3f},{opt[i]:.4f},{port[i]:.4f}\n")

rng = np.random.default_rng(2026)
z = rng.standard_normal(1_000_000)
s_t = c["spot"] * np.exp((c["r"] - 0.5 * c["vol"] ** 2) * c["t"] + c["vol"] * math.sqrt(c["t"]) * z)
pay = math.exp(-c["r"] * c["t"]) * np.maximum(s_t - c["strike"], 0.0)
formula = bs(c["spot"], c["strike"], c["t"], c["r"], c["q"], c["vol"], "C")
with open(OUT / "mc_convergence.csv", "w") as f:
    f.write("m,estimate,lo,hi,formula\n")
    for e in np.arange(2.0, 6.01, 0.25):
        m = int(round(10 ** e))
        est, se = pay[:m].mean(), pay[:m].std(ddof=1) / math.sqrt(m)
        f.write(f"{m},{est:.4f},{est - 2 * se:.4f},{est + 2 * se:.4f},{formula:.4f}\n")
