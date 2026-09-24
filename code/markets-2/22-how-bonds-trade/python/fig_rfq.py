"""Chart data for Book 2, Chapter 22 (deterministic, seeded)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rfq_demo import cost_table, histograms

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "cost.csv", "w") as f:
    f.write("n,emax,l05,l10,l15\n")
    for n, e, a, b, c in cost_table():
        f.write(f"{n},{e:.4f},{a:.3f},{b:.3f},{c:.3f}\n")
hs = histograms()
with open(OUT / "hist.csv", "w") as f:
    f.write("x," + ",".join(f"n{n}" for n, _ in hs) + "\n")
    for i in range(len(hs[0][1])):
        f.write(f"{hs[0][1][i][0]:.2f}," + ",".join(f"{h[i][1]:.5f}" for _, h in hs) + "\n")
