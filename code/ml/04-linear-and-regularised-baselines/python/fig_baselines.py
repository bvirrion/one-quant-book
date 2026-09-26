"""Chart data for Book 12, chapter 4 (deterministic)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ml_baselines import crossing, paths  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/ml" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

p = paths()
with open(OUT / "path_ridge.csv", "w") as f:
    f.write("log10alpha,ridge,splines\n")
    for a, s1, s2 in zip(p["ridge"][0], p["ridge"][1], p["ridge on splines"][1], strict=True):
        f.write(f"{math.log10(a):.2f},{100 * s1:.4f},{100 * s2:.4f}\n")
with open(OUT / "path_lasso.csv", "w") as f:
    f.write("log10alpha,lasso\n")
    for a, s1 in zip(p["lasso"][0], p["lasso"][1], strict=True):
        f.write(f"{math.log10(a):.2f},{100 * s1:.4f}\n")
with open(OUT / "crossing.csv", "w") as f:
    f.write("months,ridge,boosting,ceiling,ridge_sr,boosting_sr\n")
    for n, rg, gb, rs, gs, c in crossing():
        f.write(f"{n},{100 * rg:.4f},{100 * gb:.4f},{100 * c:.4f},{rs:.3f},{gs:.3f}\n")
