"""Chart data for Book 7, chapter 2 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_marketdata import bars_per_window, clocks, day, realised_variance, wti_series

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

tp = day()
c = clocks(tp)
counts = {k: bars_per_window(b, 900.0, tp.cfg.seconds) for k, b in c.items()}
with open(OUT / "clocks.csv", "w") as f:
    f.write("minute,time,tick,volume,dollar\n")
    for i in range(len(counts["time"])):
        f.write(f"{7.5 + 15 * i:.1f}," + ",".join(str(int(counts[k][i])) for k in ("time", "tick", "volume", "dollar"))
                + "\n")

with open(OUT / "signature.csv", "w") as f:
    f.write("seconds,trade,mid\n")
    for w in (1, 2, 3, 5, 10, 15, 20, 30, 45, 60, 90, 120, 180, 300, 450, 600, 900):
        rt, rm = realised_variance(tp, w)
        f.write(f"{w},{rt:.5f},{rm:.5f}\n")

s = wti_series()
with open(OUT / "wti.csv", "w") as f:
    f.write("year,front,held,back,ratio\n")
    for d, a, h, b, r in zip(s["dates"], s["c1"], s["held"], s["back"], s["ratio"], strict=True):
        y = d.year + (d.timetuple().tm_yday - 0.5) / 365.25
        f.write(f"{y:.4f},{a:.2f},{h:.2f},{b:.2f},{r:.2f}\n")
print("clocks", {k: (int(v.min()), int(v.max())) for k, v in counts.items()})
print("max back", round(float(np.max(s["back"])), 2))
