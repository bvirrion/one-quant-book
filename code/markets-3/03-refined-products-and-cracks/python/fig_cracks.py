"""Chart data for Book 3, Chapter 3 (deterministic, from data/markets-3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_cracks import arb_series, crack_series, seasonality

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)


def t(m: str) -> float:
    return int(m[:4]) + (int(m[5:]) - 0.5) / 12


with open(OUT / "crack321.csv", "w") as f:
    f.write("t,crack,gas,diesel\n")
    for m, c, g, d in crack_series():
        f.write(f"{t(m):.4f},{c:.2f},{g:.2f},{d:.2f}\n")
with open(OUT / "season.csv", "w") as f:
    f.write("month,gas,diesel\n")
    for m, g, d in seasonality():
        f.write(f"{m},{g:.2f},{d:.2f}\n")
with open(OUT / "arb.csv", "w") as f:
    f.write("t,cents\n")
    for m, a in arb_series():
        f.write(f"{t(m):.4f},{a:.2f}\n")
