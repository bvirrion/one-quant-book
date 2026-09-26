"""Chart data for Book 10, chapter 16 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_algos import BINS, NAMES, example_days, flow, forecast_study, vwap_study  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

v = flow()
(j0, d0), (j1, d1) = example_days()
typ = v[j0, :].sum(axis=0)
with open(OUT / "profile.csv", "w") as f:
    f.write("bin,typical,normal,news\n")
    for k in range(BINS):
        f.write(f"{k + 1},{100 * typ[k] / typ.sum():.3f},{100 * v[j0, d0, k] / v[j0, d0].sum():.3f},"
                f"{100 * v[j1, d1, k] / v[j1, d1].sum():.3f}\n")
fs = forecast_study()
with open(OUT / "forecast.csv", "w") as f:
    f.write("i,normal,high\n")
    for i, n in enumerate(NAMES):
        f.write(f"{i},{fs[n]['normal']:.3f},{fs[n]['high']:.3f}\n")
vs = vwap_study()
for label in ("high", "normal"):
    for kind in ("static", "dynamic"):
        a = vs[(label, kind)]["rows"]
        np.savetxt(OUT / f"vwap_{label}_{kind}.csv", a[:, [1, 0]], fmt="%.3f", delimiter=",", header="sched,total",
                   comments="")
