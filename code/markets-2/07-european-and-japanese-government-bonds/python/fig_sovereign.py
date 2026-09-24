"""Chart data for Book 2, Chapter 7 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from sovereign_demo import euro_spreads, nav_curve, yields

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-2/07-european-and-japanese-government-bonds"
OUT.mkdir(parents=True, exist_ok=True)


def t(date: str) -> float:
    y, m, _ = date.split("-")
    return int(y) + (int(m) - 0.5) / 12


sp = euro_spreads()
with open(OUT / "spreads.csv", "w") as f:
    f.write("t,IT,FR,ES\n")
    for (d, it), (_, fr), (_, es) in zip(sp["IT"], sp["FR"], sp["ES"], strict=True):
        f.write(f"{t(d):.4f},{it:.1f},{fr:.1f},{es:.1f}\n")

with open(OUT / "jgb.csv", "w") as f:
    f.write("t,JP\n")
    for d, v in yields()["JP"]:
        f.write(f"{t(d):.4f},{v:.3f}\n")

with open(OUT / "ldi.csv", "w") as f:
    f.write("shock,cushion\n")
    for s, c in nav_curve():
        f.write(f"{s},{c:.2f}\n")
