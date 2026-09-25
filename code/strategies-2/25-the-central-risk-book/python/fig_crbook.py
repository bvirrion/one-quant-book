"""Chart data for Book 9, chapter 25 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_crbook import RATES, by_desks, frontier  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

f, g = frontier(True), frontier(False)
with open(OUT / "frontier.csv", "w") as fh:
    fh.write("rate,cost,sd,cost_nofut,sd_nofut\n")
    for r in RATES:
        row = (f[r]["cost"], f[r]["sd"], g[r]["cost"], g[r]["sd"])
        fh.write(f"{r:.2f}," + ",".join(f"{x / 1000:.2f}" for x in row) + "\n")
with open(OUT / "desks.csv", "w") as fh:
    fh.write("desks,common,independent\n")
    for n, (a, b) in by_desks().items():
        fh.write(f"{n},{100 * a:.2f},{100 * b:.2f}\n")
