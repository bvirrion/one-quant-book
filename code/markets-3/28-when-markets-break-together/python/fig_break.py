"""Chart data for Book 3, Chapter 28 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_break import ablation_table, march_2020, price_paths

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "paths.csv", "w") as f:
    f.write("day,a1,a2,a3\n")
    for d, a, b, c in price_paths():
        f.write(f"{d},{a:.3f},{b:.3f},{c:.3f}\n")

with open(OUT / "ablations.csv", "w") as f:
    f.write("idx,multiplier\n")
    for i, (_, _, m, _) in enumerate(ablation_table(), 1):
        f.write(f"{i},{m:.3f}\n")

with open(OUT / "march2020.csv", "w") as f:
    f.write("day,ust10y,usd\n")
    for i, (_, y, u) in enumerate(march_2020()):
        f.write(f"{i},{y:.2f},{u:.4f}\n")
