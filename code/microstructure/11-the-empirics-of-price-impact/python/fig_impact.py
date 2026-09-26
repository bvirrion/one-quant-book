"""Chart data for Book 10, chapter 11 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_impact import H, counterfactual, panel, panel_fits, single_and_aggregate  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

s = single_and_aggregate()
r = s["response"]
with open(OUT / "response.csv", "w") as f:
    f.write("lag," + ",".join(f"s{k}" for k in range(4)) + "\n")
    for i, lag in enumerate(r["lags"]):
        f.write(f"{lag}," + ",".join(f"{v[i]:.4f}" for v in r["by_size"].values()) + "\n")
a = s["aggregate"]
with open(OUT / "aggregate.csv", "w") as f:
    f.write("flow,dm\n")
    for x, y in zip(a["flow"], a["dm"], strict=True):
        if not np.isnan(x):
            f.write(f"{x:.1f},{y:.4f}\n")
c = counterfactual()
with open(OUT / "meta.csv", "w") as f:
    f.write("h," + ",".join(f"m{q},e{q}" for q in (1500, 6000, 24000)) + "\n")
    f.write("0," + ",".join("0,0" for _ in range(3)) + "\n")
    for i, h in enumerate(H):
        f.write(f"{h}," + ",".join(f"{c[q][0][i]:.4f},{c[q][1][i]:.4f}" for q in (1500, 6000, 24000)) + "\n")
p = panel(1, 0.3)
fits = panel_fits()
edges = np.quantile(p["participation"], np.linspace(0, 1, 21))
idx = np.clip(np.searchsorted(edges, p["participation"], side="right") - 1, 0, 19)
with open(OUT / "sqrt.csv", "w") as f:
    f.write("x,clean,timed\n")
    y_timed = p["impact"] / p["sigma"]
    y_clean = (p["impact"] - p["forecast"]) / p["sigma"]
    for k in range(20):
        sel = idx == k
        f.write(f"{p['participation'][sel].mean():.6f},{y_clean[sel].mean():.6f},{y_timed[sel].mean():.6f}\n")
with open(OUT / "fits.csv", "w") as f:
    f.write("name,exponent,prefactor\n")
    for k in ("clean", "timed"):
        f.write(f"{k},{fits[k]['exponent']:.4f},{fits[k]['prefactor']:.4f}\n")
