"""Chart data for Book 16, chapter 6 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_head as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

f = m.fan()
with open(OUT / "fan.csv", "w") as fh:
    fh.write("month,p5,p25,p50,p75,p95,budget\n")
    fh.write("0,0,0,0,0,0,0\n")
    for mo in range(1, 13):
        p = f[mo]
        fh.write(f"{mo}," + ",".join(f"{x:.1f}" for x in p) + f",{m.PLAN.budget * mo / 12:.2f}\n")

with open(OUT / "pmeet.csv", "w") as fh:
    fh.write("k,s05,s10,s15,s20\n")
    for k in np.round(np.arange(0.5, 1.51, 0.05), 2):
        fh.write(f"{k:.2f}," + ",".join(f"{100 * m.p_meet_closed(s, k):.1f}" for s in (0.5, 1.0, 1.5, 2.0)) + "\n")
