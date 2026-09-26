"""Chart data for Book 10, chapter 25 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_halts import SECONDS, TICK, XS, example, magnet_study  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

e = example()
bt = np.array([b[0] for b in e["bands"]])
with open(OUT / "example.csv", "w") as f:
    f.write("t,mid,lo,hi\n")
    for s in np.arange(1.0, SECONDS, 1.0):
        i = max(np.searchsorted(e["t"], s, side="right") - 1, 0)
        j = max(np.searchsorted(bt, s, side="right") - 1, 0)
        f.write(f"{s:.0f},{e['mid'][i] / 100:.3f},{e['bands'][j][1] / TICK / 100:.2f},"
                f"{e['bands'][j][2] / TICK / 100:.2f}\n")
m = magnet_study()
with open(OUT / "passage.csv", "w") as f:
    f.write("x,both,band,none\n")
    for x in XS:
        f.write(f"{x},{m['band and anticipators'][x][1]:.3f},{m['band alone'][x][1]:.3f},{m['no band'][x][1]:.3f}\n")
