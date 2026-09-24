"""Chart data for Book 2, Chapter 21 (deterministic, from data/markets-2)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from credit_demo import GOVT, PATH, SWAP, interp, load_hqm, measures

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "hqm.csv", "w") as f:
    f.write("t,spread\n")
    for d, h, g in load_hqm():
        f.write(f"{int(d[:4]) + (int(d[5:7]) - 0.5) / 12:.4f},{h - g:.2f}\n")
with open(OUT / "curves.csv", "w") as f:
    f.write("t,govt,swap\n")
    for k in range(2, 31):
        f.write(f"{k},{100 * interp(GOVT, k):.4f},{100 * interp(SWAP, k):.4f}\n")
with open(OUT / "bond.csv", "w") as f:
    f.write("t,y\n")
    f.write(f"7,{100 * measures()['yield']:.4f}\n")
with open(OUT / "angel.csv", "w") as f:
    f.write("month,spread\n")
    for m, s in PATH:
        f.write(f"{m},{s:.2f}\n")
