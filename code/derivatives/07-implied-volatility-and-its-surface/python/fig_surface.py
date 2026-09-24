"""Chart data for Book 5, Chapter 7 (deterministic)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_surface import asset_class_smiles, density, forward, smile_vol

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "smiles.csv", "w") as f:
    f.write("strike,m1,m3,y1,y2\n")
    for k in range(60, 131, 2):
        vols = [100 * smile_vol(math.log(k / forward(d / 365)), d / 365) for d in (30, 91, 365, 730)]
        f.write(f"{k}," + ",".join(f"{v:.3f}" for v in vols) + "\n")

with open(OUT / "asset_classes.csv", "w") as f:
    f.write("k,equity,fx,commodity\n")
    for k, e, x, c in asset_class_smiles([i / 100 for i in range(-30, 31, 2)]):
        f.write(f"{k:.2f},{100 * e:.3f},{100 * x:.3f},{100 * c:.3f}\n")

t = 91 / 365
f0 = forward(t)
with open(OUT / "regimes.csv", "w") as f:
    f.write("strike,before,sticky_delta\n")
    for k in range(80, 121, 1):
        before = smile_vol(math.log(k / f0), t)
        after = smile_vol(math.log(k / (0.95 * f0)), t)
        f.write(f"{k},{100 * before:.3f},{100 * after:.3f}\n")

skew, flat = density(), density(flat=True)
with open(OUT / "density.csv", "w") as f:
    f.write("s,skewed,flat\n")
    for (k, a), (_, b) in zip(skew, flat, strict=True):
        if 55 <= k <= 140 and abs(k * 2 - round(k * 2)) < 1e-9 and (k * 2) % 2 == 0:
            f.write(f"{k:.1f},{a:.6f},{b:.6f}\n")
