"""Chart data for Book 11, chapter 11 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hf_hedging as h  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

LABELS = {"future, zero": "future always", "future, band 100,000": "band 100k", "future, band 250,000": "band 250k",
          "future, band 500,000": "band 500k", "future, band 1,000,000": "band 1m"}
with open(OUT / "frontier.csv", "w") as f:
    f.write("risk,cost,label\n")
    for k, v in h.frontier().items():
        lab = LABELS.get(k, k)
        f.write(f"{v['risk'] / 1000:.3f},{v['cost'] / 1000:.3f},{lab}\n")

t = h.ten_to_four()
edges = np.linspace(-30, 40, 71)
with open(OUT / "overnight.csv", "w") as f:
    f.write("loss,keep,future\n")
    a = np.histogram(t["keep_hist"] / 1000, edges)[0] / len(t["keep_hist"])
    b = np.histogram(t["future_hist"] / 1000, edges)[0] / len(t["future_hist"])
    for x, u, v in zip(0.5 * (edges[1:] + edges[:-1]), a, b, strict=True):
        f.write(f"{x:.1f},{u:.5f},{v:.5f}\n")
