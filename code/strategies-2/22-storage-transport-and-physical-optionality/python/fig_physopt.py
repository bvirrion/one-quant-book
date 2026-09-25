"""Chart data for Book 9, chapter 22 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_physopt import MONTHS, programmes, transport_strip  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

p = programmes()
base = {c: p[c]["intrinsic"] - c * p["static"]["traded"][0] for c in (0.0, 0.02)}   # the static programme
edges = np.arange(-1.0, 3.01, 0.1)


def hist(x):
    x = np.clip(np.where(np.abs(x) < 1e-9, 0.0, x), -0.999, 2.999)          # float dust at zero; tails in the end bins
    return np.histogram(x, edges)[0] / len(x) * 100


h0, h2 = hist(p[0.0]["pnl"] - base[0.0]), hist(p[0.02]["pnl"] - base[0.02])
with open(OUT / "rolling.csv", "w") as f:
    f.write("lo,free,cost2\n")
    for lo, a, b in zip(edges[:-1], h0, h2, strict=True):
        f.write(f"{lo:.2f},{a:.2f},{b:.2f}\n")
    f.write(f"{edges[-1]:.2f},{h0[-1]:.2f},{h2[-1]:.2f}\n")

t = transport_strip()
with open(OUT / "transport.csv", "w") as f:
    f.write("k,month,intrinsic,option\n")
    for k, (m, (a, b)) in enumerate(zip(MONTHS, t["by_month"], strict=True)):
        f.write(f"{k},{m},{a:.3f},{b:.3f}\n")
