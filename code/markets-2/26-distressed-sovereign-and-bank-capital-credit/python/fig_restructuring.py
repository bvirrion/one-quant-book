"""Chart data for Book 2, Chapter 26 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from restructuring_demo import holdout_curve, offer_curve

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "offer.csv", "w") as f:
    f.write("yield,withcash,bonds\n")
    for y, a, b in offer_curve():
        f.write(f"{y:.1f},{a:.4f},{b:.4f}\n")
with open(OUT / "holdout.csv", "w") as f:
    f.write("p,cac,nocac,tender\n")
    for p, a, b, t in holdout_curve():
        f.write(f"{p:.1f},{a:.4f},{b:.4f},{t:.4f}\n")
