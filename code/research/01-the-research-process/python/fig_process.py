"""Chart data for Book 7, chapter 1 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_process import LOOKBACKS, deflated_annual, p_best, ppv, search

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "ppv.csv", "w") as f:
    f.write("prior,one,two,three\n")
    for prior in np.geomspace(0.002, 0.5, 60):
        f.write(f"{prior:.5f}," + ",".join(f"{ppv(prior, 0.5, 0.05, k):.5f}" for k in (1, 2, 3)) + "\n")

with open(OUT / "best.csv", "w") as f:
    f.write("n,y1,y2,y5,y2corr\n")
    for n in np.unique(np.round(np.geomspace(1, 10_000, 60)).astype(int)):
        vals = [p_best(2.0, int(n), y) for y in (1.0, 2.0, 5.0)] + [p_best(2.0, int(n), 2.0, 0.6)]
        f.write(f"{n}," + ",".join(f"{v:.5f}" for v in vals) + "\n")

s = search()
with open(OUT / "search.csv", "w") as f:
    f.write("lookback,sr\n")
    for lb, sr in zip(LOOKBACKS, s["srs"], strict=True):
        f.write(f"{lb},{sr:.4f}\n")

with open(OUT / "deflate.csv", "w") as f:
    f.write("n,dsr\n")
    for n in np.unique(np.round(np.geomspace(1, 1000, 50)).astype(int)):
        f.write(f"{n},{deflated_annual(s['best_sr'], s['n_obs'] / 252, int(n)):.5f}\n")
print("best", s["best_lookback"], round(s["best_sr"], 3), "dsr1", round(deflated_annual(s["best_sr"], 2, 1), 4),
      "dsr50", round(deflated_annual(s["best_sr"], 2, 50), 4), "above1", int((s["srs"] > 1).sum()),
      "mean", round(float(s["srs"].mean()), 3), "log", s["log"].trial_count("reversal"))
