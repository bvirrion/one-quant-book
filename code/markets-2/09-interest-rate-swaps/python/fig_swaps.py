"""Chart data for Book 2, Chapter 9 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from swaps_demo import RATES, TENORS, curve_table, forward_5y5y, ten_year

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-2/09-interest-rate-swaps"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "curve.csv", "w") as f:
    f.write("years,zero,fwd\n")
    for y, z, fw in curve_table():
        f.write(f"{y:.1f},{z:.4f},{fw:.4f}\n")

with open(OUT / "par.csv", "w") as f:
    f.write("years,par\n")
    for n, r in zip(TENORS, RATES, strict=True):
        f.write(f"{n},{100 * r:.3f}\n")

t, fw = ten_year()["buckets"], forward_5y5y()["buckets"]
with open(OUT / "buckets.csv", "w") as f:
    f.write("i,tenor,par10,fwd5y5y\n")
    for i, (n, a, b) in enumerate(zip(TENORS, t, fw, strict=True)):
        f.write(f"{i},{n}y,{round(a / 1000, 3) + 0.0:.3f},{round(b / 1000, 3) + 0.0:.3f}\n")
