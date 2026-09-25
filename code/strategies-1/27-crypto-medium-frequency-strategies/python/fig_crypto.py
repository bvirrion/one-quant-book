"""Chart data for Book 8, chapter 27 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_crypto import funding, venues  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "funding.csv", "w") as f:
    f.write("year,funding_pct,carry_pct\n")
    for y, fu, c, _ in funding():
        f.write(f"{y},{100 * fu:.2f},{100 * c:.2f}\n")

with open(OUT / "venues.csv", "w") as f:
    f.write("k,one_pct,any_pct,mean_pct\n")
    for k, v in venues().items():
        f.write(f"{k},{100 * v['one']:.2f},{100 * v['any']:.2f},{100 * v['mean']:.2f}\n")
