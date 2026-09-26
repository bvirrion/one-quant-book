"""Chart data for Book 10, chapter 28 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_execalgo import HORIZON, SIZES, URGENCIES, ab_study, stress  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

s = ab_study()
with open(OUT / "saved.csv", "w") as f:
    f.write("k,size," + ",".join(f"u{i},se{i}" for i in range(len(URGENCIES))) + "\n")
    for k, q in enumerate(SIZES):
        f.write(f"{k},{q}," + ",".join(f"{s['cells'][(q, u)][0]:.4f},{s['cells'][(q, u)][1]:.4f}" for u in URGENCIES)
                + "\n")
with open(OUT / "attribution.csv", "w") as f:
    f.write("k,part,is,twap\n")
    for k, part in enumerate(("spread", "impact", "timing", "fees")):
        f.write(f"{k},{part},{s['attribution']['is'][part]:.4f},{s['attribution']['twap'][part]:.4f}\n")
st = stress()
grid = np.arange(0, HORIZON + 121, 2.0)
with open(OUT / "stress.csv", "w") as f:
    f.write("t,base,halt,spike,nolimit,kill\n")
    cols = []
    for k in ("base", "halt", "spike", "nolimit", "kill"):
        fl = st[k]["algo"].fills
        t = np.array([x[0] for x in fl])
        q = np.cumsum([x[2] for x in fl])
        i = np.searchsorted(t, grid, side="right") - 1
        cols.append(np.where(i >= 0, q[np.maximum(i, 0)], 0) / 1000.0)
    for j, g in enumerate(grid):
        f.write(f"{g:.0f}," + ",".join(f"{c[j]:.1f}" for c in cols) + "\n")
