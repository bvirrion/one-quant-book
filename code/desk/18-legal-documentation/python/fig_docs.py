"""Chart data for Book 16, chapter 18 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_docs as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

nav = m.nav_path()
with open(OUT / "nav.csv", "w") as f:
    f.write("day,nav,r21,r63\n")
    for t, v in enumerate(nav):
        r21 = f"{100 * (v / nav[t - 21] - 1):.3f}" if t >= 21 else "nan"
        r63 = f"{100 * (v / nav[t - 63] - 1):.3f}" if t >= 63 else "nan"
        f.write(f"{t},{v:.3f},{r21},{r63}\n")

c = m.calls()
held = {k: np.cumsum(v) for k, v in c.items()}
ex = m.exposures()
with open(OUT / "collateral.csv", "w") as f:
    f.write("day," + ",".join(f"held_{k[-1]},exp_{k[-1]}" for k in c) + "\n")
    for t in range(m.DAYS):
        f.write(f"{t}," + ",".join(f"{held[k][t]:.3f},{ex[k][t]:.3f}" for k in c) + "\n")
