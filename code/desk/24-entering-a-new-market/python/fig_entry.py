"""Chart data for Book 16, chapter 24 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_entry as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

sch, cp = m.plan()
with open(OUT / "gantt.csv", "w") as f:
    f.write("pos,task,start,months,critical\n")
    for i, t in enumerate(m.TASKS):
        s, e, _ = sch[t.name]
        f.write(f"{i},{t.name},{s:.2f},{e - s:.2f},{int(t.name in cp)}\n")

s = m.staging()
edges = np.arange(-6000, 18001, 1000)
hp, _ = np.histogram(s["plain"], edges)
hs, _ = np.histogram(s["staged"], edges)
with open(OUT / "npv.csv", "w") as f:
    f.write("mid,plain,staged\n")
    for a, b, c in zip(edges[:-1] + 500, hp, hs, strict=True):
        f.write(f"{a / 1000:.1f},{100 * b / len(s['plain']):.3f},{100 * c / len(s['plain']):.3f}\n")

with open(OUT / "threshold.csv", "w") as f:
    f.write("threshold,value,killed\n")
    for th, v, k in m.threshold_curve():
        f.write(f"{th},{v:.2f},{100 * k:.2f}\n")
