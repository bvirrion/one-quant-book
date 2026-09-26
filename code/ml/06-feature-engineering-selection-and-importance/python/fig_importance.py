"""Chart data for Book 12, chapter 6 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ml_importance import importances, stability  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/ml" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

imp = importances()
shares = {}
for k in ("gain", "perm", "drop", "shap"):
    v = np.clip(imp[k], 0, None)
    shares[k] = v / v.sum()
labels = ["x1", "x2", "x3", "x4", "x1b", "noise"]
with open(OUT / "importance.csv", "w") as f:
    f.write("i,feature,gain,perm,drop,shap\n")
    for i, lab in enumerate(labels):
        vals = [shares[k][i] if lab != "noise" else shares[k][5:].max() for k in ("gain", "perm", "drop", "shap")]
        f.write(f"{i},{lab}," + ",".join(f"{100 * v:.2f}" for v in vals) + "\n")

s = stability()
with open(OUT / "stability.csv", "w") as f:
    f.write("j,lasso,boosting,role\n")
    for j in range(len(s["lasso"]["freq"])):
        role = 1 if j < 4 else (2 if j == 4 else 0)
        f.write(f"{j},{s['lasso']['freq'][j]:.3f},{s['boosting']['freq'][j]:.3f},{role}\n")
