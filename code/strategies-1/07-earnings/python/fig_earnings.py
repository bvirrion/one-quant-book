"""Chart data for Book 8, chapter 7 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_earnings import HOLDS, car, run  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

c = car(5, 60)
with open(OUT / "car.csv", "w") as f:
    f.write("day,positive_pct,negative_pct\n")
    for k in range(len(c["positive"])):
        f.write(f"{k - 5},{100 * c['positive'][k]:.4f},{100 * c['negative'][k]:.4f}\n")

with open(OUT / "holds.csv", "w") as f:
    f.write("hold,same_day,next_day,cut_late\n")
    for h in HOLDS:
        f.write(f"{h},{run(h, 'surprise', False, 0)['sr']:.4f},{run(h, 'surprise', False, 1)['sr']:.4f},"
                f"{run(h, 'surprise', True, 1)['sr_late']:.4f}\n")
