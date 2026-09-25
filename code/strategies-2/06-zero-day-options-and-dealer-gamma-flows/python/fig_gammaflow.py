"""Chart data for Book 9, chapter 6 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_gammaflow import days, regimes  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

_, d = days()
with open(OUT / "estimate.csv", "w") as f:
    f.write("true,convention\n")
    for t, e in zip(d["true_gamma"][:400], d["est_gamma"][:400], strict=True):
        f.write(f"{t:.2f},{e:.2f}\n")

g = regimes()
with open(OUT / "regimes.csv", "w") as f:
    f.write("x,short,long\n")
    for i, name in enumerate(("true", "convention", "average sides")):
        f.write(f"{i + 1},{g[name]['short_mean']:.2f},{g[name]['long_mean']:.2f}\n")
