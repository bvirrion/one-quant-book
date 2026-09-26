"""Chart data for Book 12, chapter 2 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ml_labels import H, events, meta  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/ml" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

e = events(1)
# an event of asset 0 whose long trade is stopped out although the ten-day return ends positive
i = int(np.flatnonzero((e["asset"] == 0) & (e["hit"] == "down") & (e["side"] * e["fh_ret"] > 0) & (e["side"] > 0))[0])
sys.path.insert(0, str(HERE.parents[3] / "firm" / "mlsynth"))
from firm_mlsynth import SeriesConfig, series  # noqa: E402

r = series(SeriesConfig(seed=1))["r"][:, 0]
t0, w = int(e["t0"][i]), float(e["width"][i])
path = np.concatenate([[0.0], np.cumsum(r[t0 + 1:t0 + H + 1])])
with open(OUT / "path.csv", "w") as f:
    f.write("day,ret,up,down\n")
    for d, x in enumerate(path):
        f.write(f"{d},{100 * x:.4f},{100 * w:.4f},{-100 * w:.4f}\n")
with open(OUT / "path_meta.csv", "w") as f:
    f.write("t0,touch,width\n")
    f.write(f"{t0},{int(e['tb_t1'][i]) - t0},{100 * w:.4f}\n")

with open(OUT / "meta.csv", "w") as f:
    f.write("threshold,share,hit,mean,t\n")
    p = meta(1)["primary"]
    f.write(f"0.00,{100 * p['share']:.2f},{100 * p['hit']:.2f},{p['mean']:.4f},{p['t']:.3f}\n")
    for th in (0.50, 0.51, 0.52, 0.53, 0.54, 0.55):
        q = meta(1, th)["meta"]
        f.write(f"{th:.2f},{100 * q['share']:.2f},{100 * q['hit']:.2f},{q['mean']:.4f},{q['t']:.3f}\n")
