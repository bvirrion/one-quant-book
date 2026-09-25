"""Chart data for Book 9, chapter 26 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_deltaone import dividends, market  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

cfg, sim = market()
with open(OUT / "spread.csv", "w") as f:
    f.write("year,spread\n")
    for t in range(0, 3 * 252):
        f.write(f"{t / 252:.4f},{sim['spread'][t]:.2f}\n")
d = dividends()
with open(OUT / "dividends.csv", "w") as f:
    f.write("year,expected,futures\n")
    for y, (e, p) in enumerate(zip(d["expected"], d["futures"], strict=True), 1):
        f.write(f"{y},{e:.2f},{p:.2f}\n")
