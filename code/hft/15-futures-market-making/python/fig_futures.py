"""Chart data for Book 11, chapter 15 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hf_futures as h  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

g = h.game()
with open(OUT / "overquote.csv", "w") as f:
    f.write("n,factor,u_eq,u_fifo\n")
    for n, r in g["rows"].items():
        f.write(f"{n},{r['factor']:.3f},{r['u_eq']:.3f},{r['u_fifo']:.3f}\n")

with open(OUT / "implied.csv", "w") as f:
    f.write("lag,per1000\n")
    for lag, r in h.implied().items():
        f.write(f"{lag},{r['per_1000']:.3f}\n")
