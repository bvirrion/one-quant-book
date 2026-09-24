"""Chart data for Book 2, Chapter 23 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from cds_demo import BIDS, OFFERS, order_book, survival_curves, upfront_curve

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "upfront.csv", "w") as f:
    f.write("spread,c100,c500\n")
    for s, a, b in upfront_curve():
        f.write(f"{s},{a:.4f},{b:.4f}\n")
with open(OUT / "survival.csv", "w") as f:
    f.write("t,s100,s300,s800\n")
    for t, *q in survival_curves():
        f.write(f"{t:.2f}," + ",".join(f"{x:.5f}" for x in q) + "\n")
with open(OUT / "lehman.csv", "w") as f:
    f.write("dealer,bid,offer\n")
    for k, (b, o) in enumerate(zip(BIDS, OFFERS, strict=True), start=1):
        f.write(f"{k},{b},{o}\n")
with open(OUT / "orders.csv", "w") as f:
    f.write("price,size,cum\n")
    for p, s, c in order_book():
        f.write(f"{p},{s:.0f},{c:.0f}\n")
