"""Chart data for Book 8, chapter 8 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_lending import START, YEAR, book, squeeze  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

b = book("si")
cum = {k: np.cumsum(b[k]) for k in ("gross", "after_fee", "net")}
with open(OUT / "book.csv", "w") as f:
    f.write("year,gross,after_fee,net\n")
    for i in range(0, len(cum["net"]), 5):
        f.write(f"{(START + i) / YEAR:.3f}," + ",".join(f"{100 * cum[k][i]:.3f}" for k in cum) + "\n")

sq = squeeze()
edges = np.arange(-0.10, 0.0301, 0.01)
with open(OUT / "squeeze.csv", "w") as f:
    f.write("bin,squeeze,actual\n")
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        n1 = int(((sq["losses"] >= lo) & (sq["losses"] < hi)).sum())
        n2 = int(((sq["actual"] >= lo) & (sq["actual"] < hi)).sum())
        f.write(f"{100 * (lo + hi) / 2:.1f},{n1},{n2}\n")
