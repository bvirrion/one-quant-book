"""Chart data for Book 7, chapter 19 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_simlive import decomposition, steps  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

rows, mean = decomposition()
with open(OUT / "waterfall.csv", "w") as f:
    f.write("k,level,low,high\n")
    prev = 0.0
    for k, (_, v, _d) in enumerate(steps(mean)):
        lo, hi = (min(prev, v), max(prev, v)) if k else (min(0.0, v), max(0.0, v))
        f.write(f"{k},{v:.3f},{lo:.3f},{hi:.3f}\n")
        prev = v
with open(OUT / "sessions.csv", "w") as f:
    f.write("session,sim,live,chance\n")
    for i, r in enumerate(rows):
        f.write(f"{i + 1},{r['sim']:.2f},{r['live']:.2f},{r['chance']:.2f}\n")
