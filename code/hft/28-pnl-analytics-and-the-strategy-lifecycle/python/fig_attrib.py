"""Chart data for Book 11, chapter 28 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hf_attrib as h  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

d = h.daily()
roll = np.convolve(d, np.ones(20) / 20, mode="full")[: len(d)]
with open(OUT / "daily.csv", "w") as f:
    f.write("day,pnl,roll\n")
    for i, (x, r) in enumerate(zip(d, roll, strict=True)):
        f.write(f"{i},{x / 1000:.3f},{(r / 1000) if i >= 19 else float('nan'):.3f}\n")

m = h.month9()
with open(OUT / "month9.csv", "w") as f:
    f.write("i,factor,truth,estimate\n")
    for i, k in enumerate(("spread", "volume", "competition", "parameter", "residual")):
        f.write(f"{i},{k},{m['truth'][k] / 1000:.2f},{m['estimate'][k] / 1000:.2f}\n")

c = h.cusum_path()
with open(OUT / "cusum.csv", "w") as f:
    f.write("day,share,cusum\n")
    y = h.year()
    for i in range(150, 200):
        f.write(f"{i},{100 * y.share[i, 1]:.3f},{c[i]:.4f}\n")
