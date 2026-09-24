"""Chart data for Book 3, Chapter 24 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_business import fee_by_vol, hedge_curves

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "fee.csv", "w") as f:
    f.write("vol,fee\n")
    for v, fee in fee_by_vol():
        f.write(f"{100 * v:.0f},{100 * fee:.3f}\n")

with open(OUT / "hedge.csv", "w") as f:
    f.write("price,t1,t05\n")
    for p, a, b in hedge_curves():
        f.write(f"{p:.2f},{a / 1e6:.4f},{b / 1e6:.4f}\n")
