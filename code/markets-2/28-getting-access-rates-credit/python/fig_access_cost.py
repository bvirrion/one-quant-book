"""Chart data for Book 2, Chapter 28 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from access_cost_demo import cost_curves, sensitivity

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "costs.csv", "w") as f:
    f.write("repo,rent,buy,bilateral\n")
    for b, *c in cost_curves():
        f.write(f"{b:.1f}," + ",".join(f"{x:.4f}" for x in c) + "\n")
with open(OUT / "sensitivity.csv", "w") as f:
    f.write("spread,breakeven\n")
    for s, b in sensitivity():
        f.write(f"{s:.1f},{b:.4f}\n")
