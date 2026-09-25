"""Chart data for Book 7, chapter 15 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_forecast import calibration, law  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

c = calibration()
ms, mr, pred = c["bins"]
with open(OUT / "calibration.csv", "w") as f:
    f.write("score,realised,predicted\n")
    for a, b, p in zip(ms, mr, pred, strict=True):
        f.write(f"{a:.4f},{b:.5f},{p:.5f}\n")
grid, iso = c["iso"]
with open(OUT / "isotonic.csv", "w") as f:
    f.write("score,fit\n")
    for g, v in zip(grid, iso, strict=True):
        f.write(f"{g:.2f},{v:.5f}\n")

lw = law()
with open(OUT / "shortfall.csv", "w") as f:
    f.write("k,ir\n")
    for k, v in enumerate([lw["law"], lw["ir_gauss"], lw["qian_hua"], lw["ir_market"], lw["steps"][2], lw["ir_long"]]):
        f.write(f"{k},{v:.4f}\n")
