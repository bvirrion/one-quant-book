"""Chart data for Book 8, chapter 14 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_intraml import HORIZONS, naive, scores, trading  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "r2.csv", "w") as f:
    f.write("h,ridge,gbm\n")
    for h in HORIZONS:
        s = scores(h)
        f.write(f"{h},{100 * s['r2_ridge']:.3f},{100 * s['r2_gbm']:.3f}\n")

with open(OUT / "pnl.csv", "w") as f:
    f.write("h,naive_aggressive,passive,coupled\n")
    for h in HORIZONS:
        f.write(f"{h},{naive(h)['agg_mean']:.4f},{naive(h)['pas_mean']:.4f},{trading(h)['coupled']:.4f}\n")
