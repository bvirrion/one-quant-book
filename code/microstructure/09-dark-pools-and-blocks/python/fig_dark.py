"""Chart data for Book 10, chapter 9 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_dark import STRATEGIES, compare  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

c = compare()
with open(OUT / "costs.csv", "w") as f:
    f.write("k,shortfall,shortfall_se,drift,drift_se,own,leak\n")
    for k, s in enumerate(STRATEGIES):
        v = c[s]
        f.write(f"{k},{v['shortfall'][0]:.3f},{v['shortfall'][1]:.3f},{v['drift'][0]:.3f},{v['drift'][1]:.3f},"
                f"{v['own_impact'][0]:.3f},{v['leakage'][0]:.3f}\n")
