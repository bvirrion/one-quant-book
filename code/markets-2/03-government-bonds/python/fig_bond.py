"""Chart data for Book 2, Chapter 3 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bond_demo import TEN, Y10, price_yield_curve, year_of_prices, zero_curve

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-2/03-government-bonds"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "priceyield.csv", "w") as f:
    f.write("yield,price,duration,convexity\n")
    for y, p, lin, quad in price_yield_curve(TEN, Y10):
        f.write(f"{y:.4f},{p:.4f},{lin:.4f},{quad:.4f}\n")

with open(OUT / "cleandirty.csv", "w") as f:
    f.write("day,clean,dirty\n")
    for d, c, di in year_of_prices(TEN, Y10):
        f.write(f"{d},{c:.4f},{di:.4f}\n")

with open(OUT / "zero.csv", "w") as f:
    f.write("years,par,zero\n")
    for t, p, z in zero_curve():
        f.write(f"{t:.1f},{p:.4f},{z:.4f}\n")
