"""Chart data for Book 8, chapter 4 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_pairs import START, YEAR, calibration, run, takeover  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

ex = takeover()
with open(OUT / "takeover.csv", "w") as f:
    f.write("day,spread,pnl\n")
    for d, (s, p) in enumerate(zip(ex["spread"], ex["pnl"], strict=True)):
        f.write(f"{d},{s:.5f},{p:.5f}\n")

with open(OUT / "calibration.csv", "w") as f:
    f.write("nominal,actual\n")
    for x, v in calibration().items():
        f.write(f"{x},{v:.5f}\n")

books = ("distance", "copula", "two-step", "eg", "twin")
cum = {b: np.cumsum(run(0.1, b)["net"]) for b in books}
with open(OUT / "books.csv", "w") as f:
    f.write("year," + ",".join(b.replace("-", "") for b in books) + "\n")
    for i in range(0, len(cum["distance"]), 5):
        f.write(f"{(START + i) / YEAR:.3f}," + ",".join(f"{100 * cum[b][i]:.3f}" for b in books) + "\n")
