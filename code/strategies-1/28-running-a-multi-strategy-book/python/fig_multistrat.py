"""Chart data for Book 8, chapter 28 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_multistrat import LIMITS, limits, paths  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "paths.csv", "w") as f:
    f.write("year,none,cap\n")
    for y, a, b in paths():
        f.write(f"{y:.3f},{100 * a:.2f},{100 * b:.2f}\n")

with open(OUT / "stops.csv", "w") as f:
    f.write("limit_pct,paths_pct,firm_pct\n")
    for lim in LIMITS:
        v = limits(lim)
        f.write(f"{100 * lim:.0f},{100 * v['paths']:.2f},{100 * v['per_pod_year']:.2f}\n")
