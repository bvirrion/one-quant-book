"""Chart data for Book 7, chapter 14 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_combine import geometry, small_universe  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

measured, theory, ic, c = geometry()
with open(OUT / "geometry.csv", "w") as f:
    f.write("k,measured,theory,ceiling\n")
    for k in measured:
        f.write(f"{k},{measured[k]:.5f},{theory[k]:.5f},{ic / np.sqrt(c):.5f}\n")

s, d = small_universe("stable", 12), small_universe("drifting", 12)
with open(OUT / "shrink.csv", "w") as f:
    f.write("lam,stable,drifting,stable_icw,drifting_icw\n")
    for lam in s["shrunk"]:
        f.write(f"{lam:.1f},{s['shrunk'][lam]:.5f},{d['shrunk'][lam]:.5f},{s['ic_weighted']:.5f},{d['ic_weighted']:.5f}\n")
