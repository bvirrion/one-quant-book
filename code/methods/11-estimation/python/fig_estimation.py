"""Chart data for Book 4, Chapter 11 (deterministic, seeded)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_estimation import HOLD, SD_BP, coverage, lrv_factor, mean_se, misspecified_fit, strategy_pnl, years_for_t

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

x = strategy_pnl(seed=189)
with open(OUT / "acf.csv", "w") as f:
    f.write("lag,sample,theory\n")
    for k in range(1, 11):
        f.write(f"{k},{np.corrcoef(x[k:], x[:-k])[0, 1]:.4f},{max(0.0, 1 - k / HOLD):.4f}\n")

se_true = SD_BP * math.sqrt(lrv_factor() / x.size)
with open(OUT / "nwlags.csv", "w") as f:
    f.write("lags,nw,iid,true\n")
    for L in range(0, 31):
        f.write(f"{L},{mean_se(x, 'hac', lags=L):.4f},{mean_se(x, 'iid'):.4f},{se_true:.4f}\n")

c = coverage()
with open(OUT / "coverage.csv", "w") as f:
    f.write("k,method,coverage\n")
    p = c["pct"]
    f.write(f"0,iid,{p['iid']:.1f}\n1,NW(7),{p['nw']:.1f}\n2,NW(20),{p['nw20']:.1f}\n")

m = misspecified_fit()
reps = np.array([math.log(np.random.default_rng(1000 + k).standard_t(6, 2000).std()) for k in range(4000)])
centre = reps.mean()
edges = np.linspace(centre - 0.1, centre + 0.1, 41)
h = np.histogram(reps, bins=edges)[0] / (reps.size * np.diff(edges))
with open(OUT / "sandwich.csv", "w") as f:
    f.write("x,hist,hessian,sandwich\n")
    for i in range(h.size):
        mid = 0.5 * (edges[i] + edges[i + 1])
        dens = [math.exp(-0.5 * ((mid - centre) / s) ** 2) / (s * math.sqrt(2 * math.pi))
                for s in (m["logsd_se_hessian"], m["logsd_se_sandwich"])]
        f.write(f"{mid - centre:.4f},{h[i]:.4f},{dens[0]:.4f},{dens[1]:.4f}\n")


with open(OUT / "years.csv", "w") as f:
    f.write("sr,iid,overlap\n")
    for sr in np.linspace(0.5, 3.0, 26):
        f.write(f"{sr:.2f},{years_for_t(sr):.3f},{years_for_t(sr, lrv_factor()):.3f}\n")
