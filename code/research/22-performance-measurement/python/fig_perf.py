"""Chart data for Book 7, chapter 22 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_perf import MONTH, YEAR, dd_probability, histories, monthly_scatter  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "perf"))
from firm_perf import drawdown  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

h = histories()
daily = {k: h[k] for k in ("trend", "short vol", "market maker")}
sm = np.repeat(h["smoothed"], MONTH)                                   # a monthly book plotted on the daily axis
with open(OUT / "paths.csv", "w") as f:
    f.write("year,trend,shortvol,mm,smoothed,dd_trend,dd_shortvol,dd_mm,dd_smoothed\n")
    w = {k: np.cumprod(1 + v) for k, v in daily.items()}
    ws = np.cumprod(1 + h["smoothed"])
    dd = {k: drawdown(v) for k, v in daily.items()}
    dds = drawdown(h["smoothed"])
    for t in range(0, len(sm), 3):
        m = t // MONTH
        f.write(f"{(t + 1) / YEAR:.4f},{w['trend'][t]:.4f},{w['short vol'][t]:.4f},{w['market maker'][t]:.4f},"
                f"{ws[m]:.4f},{dd['trend'][t]:.4f},{dd['short vol'][t]:.4f},{dd['market maker'][t]:.4f},"
                f"{dds[m]:.4f}\n")

years = tuple(range(1, 11))
pt, ps = dd_probability("trend", years=years), dd_probability("short vol", years=years)
with open(OUT / "ddprob.csv", "w") as f:
    f.write("years,trend,shortvol\n")
    for y in years:
        f.write(f"{y},{pt[y]:.4f},{ps[y]:.4f}\n")

a, b, _ = monthly_scatter()
with open(OUT / "scatter.csv", "w") as f:
    f.write("index,shortvol\n")
    for x, y in zip(a, b, strict=True):
        f.write(f"{x:.4f},{y:.4f}\n")
