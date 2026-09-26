"""Chart data for Book 11, chapter 1 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
from hf_business import HORIZONS, SMALL, markout_curve, waterfall  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "waterfall.csv", "w") as f:
    f.write("k,label,bottom,cost,total\n")
    level = 0.0
    for k, (label, x) in enumerate(waterfall()):
        if x > 0:
            f.write(f"{k},{label},0.0,0.0,{x:.1f}\n")
        else:
            f.write(f"{k},{label},{level + x:.1f},{-x:.1f},0.0\n")
        level += x
    f.write(f"{k + 1},what remains,0.0,0.0,{level:.1f}\n")

mid, truth = markout_curve("mid"), markout_curve("truth")
with open(OUT / "markout.csv", "w") as f:
    f.write("h,mid,truth\n")
    for h, a, b in zip(HORIZONS, mid, truth, strict=True):
        f.write(f"{h},{a:.3f},{b:.3f}\n")

with open(OUT / "breakeven.csv", "w") as f:
    f.write("volume_bn,profit_k\n")
    for v in np.arange(0.0, 3.01, 0.25):
        p = (SMALL["capture"] - SMALL["variable"]) * v * 1e9 - SMALL["fixed"]
        f.write(f"{v:.2f},{p / 1e3:.1f}\n")
