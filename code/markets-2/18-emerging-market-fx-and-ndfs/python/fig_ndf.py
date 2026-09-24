"""Chart data for Book 2, Chapter 18 (deterministic, from data/markets-2)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ndf_demo import load_eurchf, unpeg

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "eurchf.csv", "w") as f:
    f.write("t,eurchf\n")
    for d, v in load_eurchf():
        y, m, dd = int(d[:4]), int(d[5:7]), int(d[8:10])
        f.write(f"{y + (m - 1) / 12 + (dd - 1) / 365:.4f},{v:.4f}\n")
with open(OUT / "leverage.csv", "w") as f:
    f.write("k,leverage,multiple\n")
    for k, (lev, mult) in enumerate(unpeg()["by_leverage"].items()):
        f.write(f"{k},{lev},{mult:.3f}\n")
