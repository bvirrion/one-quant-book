"""Chart data for Book 8, chapter 11 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_mergerarb import run  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

r = run()
with open(OUT / "months.csv", "w") as f:
    f.write("market_pct,deals_pct\n")
    for m, x in zip(r["mm"], r["rm"], strict=True):
        f.write(f"{100 * m:.3f},{100 * x:.3f}\n")
