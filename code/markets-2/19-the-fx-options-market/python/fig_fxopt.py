"""Chart data for Book 2, Chapter 19 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from fxopt_demo import USDJPY, barrier_curve, delta_curves, smile, smile_curve

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

a, b = smile_curve(USDJPY, "spot", False), smile_curve(USDJPY, "spot_pa", True)
with open(OUT / "smile_usdjpy.csv", "w") as f:
    f.write("k_reg,v_reg,k_pa,v_pa\n")
    for (k1, v1), (k2, v2) in zip(a, b, strict=True):
        f.write(f"{k1:.3f},{100 * v1:.4f},{k2:.3f},{100 * v2:.4f}\n")
with open(OUT / "barrier.csv", "w") as f:
    f.write("s,pips,delta\n")
    for s, v, d in barrier_curve():
        f.write(f"{s:.5f},{v:.3f},{d:.4f}\n")

with open(OUT / "deltas.csv", "w") as f:
    f.write("k,reg,pa\n")
    for k, d1, d2 in delta_curves():
        f.write(f"{k:.2f},{d1:.4f},{d2:.4f}\n")
with open(OUT / "quotes.csv", "w") as f:
    f.write("x,vol\n")
    sm = smile(USDJPY, "spot_pa", True)
    for x, v in ((-25, sm["vol_p"]), (0, USDJPY["atm"]), (25, sm["vol_c"])):
        f.write(f"{x},{100 * v:.2f}\n")
