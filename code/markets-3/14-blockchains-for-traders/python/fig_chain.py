"""Chart data for Book 3, Chapter 14 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_chain import demand_shock

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "shock.csv", "w") as f:
    f.write("block,base,share\n")
    for n, b, s in demand_shock():
        f.write(f"{n},{b:.4f},{100 * s:.1f}\n")
