"""Chart data for Book 9, chapter 17 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_macrobook import stops, table  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

t = table()
with open(OUT / "expressions.csv", "w") as f:
    f.write("x,mean,lose\n")
    for i, k in enumerate(("futures", "futures, stop 25", "futures, stop 50", "option at the money",
                           "option out of the money", "option spread")):
        f.write(f"{i + 1},{t[k]['mean']:.3f},{t[k]['lose_when_right']:.3f}\n")

with open(OUT / "stops.csv", "w") as f:
    f.write("stop,share\n")
    for d, s in stops((5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 100)).items():
        f.write(f"{d},{100 * s:.2f}\n")
