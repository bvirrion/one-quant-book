"""Chart data for Book 7, chapter 20 (deterministic)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_overfit import SEARCH, SLOW, YEAR, systems  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "overfit"))
from firm_overfit import cscv, min_backtest_length  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)


def sr(x):
    return x.mean(axis=0) / x.std(axis=0) * math.sqrt(YEAR)


for world in ("noise", "trend"):
    M, _ = systems(world)
    start, cut = max(SLOW), SEARCH * YEAR
    a, b = sr(M[start:cut]), sr(M[cut:])
    with open(OUT / f"scatter_{world}.csv", "w") as f:
        f.write("is,oos\n")
        for x, y in zip(a[::4], b[::4], strict=True):
            f.write(f"{x:.4f},{y:.4f}\n")
    lg = cscv(M[start:cut], 16, max_splits=3000, seed=1)["logits"]
    h, e = np.histogram(lg, bins=np.linspace(-6, 6, 25))
    with open(OUT / f"logits_{world}.csv", "w") as f:
        f.write("x,share\n")
        for c, n in zip(0.5 * (e[:-1] + e[1:]), h, strict=True):
            f.write(f"{c:.3f},{n / len(lg):.4f}\n")

with open(OUT / "minbtl.csv", "w") as f:
    f.write("trials,sr05,sr10,sr18\n")
    for n in (2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000):
        ys = [f"{min_backtest_length(n, s):.3f}" for s in (0.5, 1.0, 1.8)]
        f.write(f"{n}," + ",".join(ys) + "\n")
