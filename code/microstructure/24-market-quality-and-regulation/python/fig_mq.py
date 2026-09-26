"""Chart data for Book 10, chapter 24 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_mq import DAYS, EVENT, study  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

s = study()
with open(OUT / "daily.csv", "w") as f:
    f.write("day,treated,control\n")
    for d in range(DAYS):
        f.write(f"{d - EVENT},{s['daily'][True][d]:.4f},{s['daily'][False][d]:.4f}\n")
with open(OUT / "event.csv", "w") as f:
    f.write("day,coef,se\n")
    for d in range(DAYS):
        c, e = s["event"].get(d, (0.0, 0.0))
        f.write(f"{d - EVENT},{c:.4f},{e:.4f}\n")
