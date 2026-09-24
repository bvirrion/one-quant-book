"""Chart data for Book 3, Chapter 26 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_data import simulate

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "loss.csv", "w") as f:
    f.write("p,silent,stale\n")
    for p in (1e-4, 3e-4, 1e-3, 3e-3, 1e-2):
        r = simulate(p, n=100_000)
        f.write(f"{100 * p:.3f},{100 * r['silent_wrong']:.4f},{100 * r['stale']:.4f}\n")
