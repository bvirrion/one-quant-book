"""Chart data for Book 2, Chapter 16 (deterministic, from data/markets-2)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from fxfwd_demo import hedged_series, load_swaplines, points_curve

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)


def t(d: str) -> float:
    return int(d[:4]) + (int(d[5:7]) - 0.5) / 12


with open(OUT / "points.csv", "w") as f:
    f.write("days,nobasis,basis\n")
    for _, d, a, b in points_curve():
        f.write(f"{d},{a:.2f},{b:.2f}\n")
with open(OUT / "hedged.csv", "w") as f:
    f.write("t,ust,hedged,jgb\n")
    for d, u, h, g in hedged_series():
        f.write(f"{t(d):.4f},{u:.2f},{h:.4f},{g:.4f}\n")
with open(OUT / "swaplines.csv", "w") as f:
    f.write("t,bn\n")
    for d, v in load_swaplines():
        if d >= "2007-01":
            f.write(f"{t(d):.4f},{v:.1f}\n")
