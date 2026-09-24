"""Chart data for Book 4, Chapter 16 (deterministic, seeded)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_linreg import LAMS, factor_months, fit_all, hedge, lasso_path, panel_truth

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

b = factor_months()["betas"]
with open(OUT / "betas.csv", "w") as f:
    f.write("month,b1,b2,sum\n")
    for m in range(b.shape[0]):
        f.write(f"{m + 1},{b[m, 0]:.4f},{b[m, 1]:.4f},{b[m, 0] + b[m, 1]:.4f}\n")

path = lasso_path()
with open(OUT / "path.csv", "w") as f:
    f.write("lam," + ",".join(f"b{j}" for j in range(path.shape[1])) + "\n")
    for lam, row in zip(LAMS, path, strict=True):
        f.write(f"{lam:.6g}," + ",".join(f"{v:.5f}" for v in row) + "\n")

A = fit_all()
with open(OUT / "cv.csv", "w") as f:
    f.write("lam,ridge,lasso,enet\n")
    for i, lam in enumerate(LAMS):
        f.write(f"{lam:.6g},{A['ridge']['cv'][i]:.6f},{A['lasso']['cv'][i]:.6f},{A['enet']['cv'][i]:.6f}\n")

rows = np.array([[hedge(30_000 + s)[k] for k in ("b_ols", "b_corrected", "b_week")] for s in range(2000)])
edges = np.linspace(0.5, 1.2, 36)
with open(OUT / "hedge.csv", "w") as f:
    f.write("h,ols,roll,weekly\n")
    for i in range(edges.size - 1):
        c = [np.sum((rows[:, j] >= edges[i]) & (rows[:, j] < edges[i + 1])) / (rows.shape[0] * (edges[1] - edges[0]))
             for j in range(3)]
        f.write(f"{0.5 * (edges[i] + edges[i + 1]):.3f},{c[0]:.4f},{c[1]:.4f},{c[2]:.4f}\n")

T = panel_truth()
with open(OUT / "panel.csv", "w") as f:
    f.write("k,method,se\n")
    for k, (name, v) in enumerate((("true sd", T["sd_ols"]), ("classical", T["classical"]), ("White", T["hc"]),
                                   ("clustered by firm", T["cluster"]), ("Fama-MacBeth", T["fm"]),
                                   ("Fama-MacBeth NW", T["fm_nw"]))):
        f.write(f"{k},{name},{v:.3f}\n")
