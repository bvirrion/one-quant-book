"""Chart data for Book 12, chapter 5 (deterministic)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ml_trees import FIT, VAL, _complexity, _xy, data, early, partial_dependence, tuning  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/ml" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

P = data()
_, yv = _xy(P, VAL)
ey = float(np.mean(yv**2))
e = early()
with open(OUT / "early.csv", "w") as f:
    f.write("trees,lr01,lr001\n")
    for t in range(0, 600, 10):
        a, b = e[0.1]["curve"][t], e[0.01]["curve"][t]
        f.write(f"{t + 1},{100 * (1 - a / ey):.4f},{100 * (1 - b / ey):.4f}\n")

tu = tuning()
rows = {i: f"{math.log10(_complexity(c)):.4f},{100 * s:.4f}\n"
        for i, (c, s) in enumerate(zip(tu["configs"], tu["scores"], strict=True))}
for name, keep in (("tuning", [i for i in rows if i not in (tu["best"], tu["plateau"])]),
                   ("tuning_best", [tu["best"]]), ("tuning_plateau", [tu["plateau"]])):
    with open(OUT / f"{name}.csv", "w") as f:
        f.write("complexity,score\n" + "".join(rows[i] for i in keep))
with open(OUT / "tuning_default.csv", "w") as f:
    f.write("complexity,score\n")
    dc = _complexity({"num_leaves": 15, "n_estimators": 300, "learning_rate": 0.03, "min_child_samples": 200})
    for s in tu["default_seeds"]:
        f.write(f"{math.log10(dc):.4f},{100 * s:.4f}\n")

with open(OUT / "pdp.csv", "w") as f:
    f.write("x,free,mono\n")
    for x, a, b in partial_dependence():
        f.write(f"{x:.4f},{a:.5f},{b:.5f}\n")
del FIT
