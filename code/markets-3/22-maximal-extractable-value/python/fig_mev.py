"""Chart data for Book 3, Chapter 22 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_mev import by_tolerance, profit_curve

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "tolerance.csv", "w") as f:
    f.write("tol_pct,gross_k,loss_k\n")
    for t, _, g, _, loss in by_tolerance(tuple(range(0, 201, 10))):
        f.write(f"{t / 100:.2f},{g / 1000:.3f},{loss * 3000 / 1000:.3f}\n")

with open(OUT / "curve.csv", "w") as f:
    f.write("front_k,gross_k,feasible_k\n")
    for a, g, ok in profit_curve(50):
        f.write(f"{a / 1000:.3f},{g / 1000:.3f},{f'{g / 1000:.3f}' if ok else 'nan'}\n")
