"""Chart data for Book 17, chapter 30."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_choose as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
r = a.results()
with open(OUT / "ranks.csv", "w") as f:
    f.write("pos,offer,r1,r2,r3,r4\n")
    for i, o in enumerate(a.OFFERS):
        f.write(f"{i + 1},{o}," + ",".join(f"{100 * x:.1f}" for x in r["ra"][i]) + "\n")
s, w = a.scaled(), r["weights"]
with open(OUT / "sweep.csv", "w") as f:
    f.write("w," + ",".join(o.replace(" ", "_") for o in a.OFFERS) + "\n")
    for x in np.linspace(0.0, 0.95, 39):
        v = a.fd.value(s, a.fd._shifted(w, a.PAY_RISK, float(x)))
        f.write(f"{x:.3f}," + ",".join(f"{y:.4f}" for y in v) + "\n")
