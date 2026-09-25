"""Chart data for Book 9, chapter 27 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_qis import complexity, path  # noqa: E402

YEAR = 252

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

p = path()
with open(OUT / "path.csv", "w") as f:
    f.write("year,cum\n")
    for t in range(0, len(p["cum"]), 5):
        f.write(f"{(t + 1) / YEAR - 10:.3f},{100 * p['cum'][t]:.2f}\n")
with open(OUT / "complexity.csv", "w") as f:
    f.write("candidates,backtest,net\n")
    for n, c in complexity().items():
        f.write(f"{n},{c['backtest']:.3f},{c['net']:.3f}\n")
