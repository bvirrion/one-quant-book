"""Chart data for Chapter 13 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from auction_sim import EXAMPLE, curves, imbalance_impact, indicative_path, random_book

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/13-auctions"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "curves.csv", "w") as f:
    f.write("price,demand,supply\n")
    f.writelines(f"{p},{d},{s}\n" for p, d, s in curves(EXAMPLE, 997, 1005))

with open(OUT / "indicative.csv", "w") as f:
    f.write("step,price,volume_k,surplus_k\n")
    for k, p, v, s in indicative_path(random_book(600, 13), 1000):
        f.write(f"{k},{p if p is not None else 'nan'},{v / 1000:.1f},{s / 1000:.1f}\n")

with open(OUT / "impact.csv", "w") as f:
    f.write("imbalance_pct,move_ticks\n")
    for pct in (0, 5, 10, 20, 30, 40, 50, 75, 100):
        f.write(f"{pct},{imbalance_impact(60, pct / 100):.3f}\n")
