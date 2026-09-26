"""Chart data for Book 11, chapter 2 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from hf_fairvalue import by_lag, window  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "lags.csv", "w") as f:
    f.write("lag,micro,consolidated,cross,cross_filter\n")
    for lag, row in by_lag().items():
        cols = ("micro", "consolidated", "cross", "cross_filter")
        f.write(f"{lag}," + ",".join(f"{row[k]:.2f}" for k in cols) + "\n")

w = window()
with open(OUT / "window.csv", "w") as f:
    f.write("t,truth,mid,cross\n")
    for i in range(len(w["t"])):
        f.write(f"{w['t'][i]:.1f},{w['truth'][i]:.2f},{w['mid'][i]:.2f},{w['cross'][i]:.3f}\n")
