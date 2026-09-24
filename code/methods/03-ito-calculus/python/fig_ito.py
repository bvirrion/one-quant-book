"""Chart data for Book 4, Chapter 3 (deterministic, seeded)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_ito import backtest, gbm_quantiles, sums_table

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

w1, rows = sums_table()
with open(OUT / "sums.csv", "w") as f:
    f.write("n,left,right,mid,ito,strat,rlim\n")
    for n, left, right, mid in rows:
        f.write(f"{n},{left:.5f},{right:.5f},{mid:.5f},{(w1**2 - 1) / 2:.5f},{w1**2 / 2:.5f},{(w1**2 + 1) / 2:.5f}\n")

b = backtest()
with open(OUT / "backtest.csv", "w") as f:
    f.write("year,honest,cheat,cov\n")
    for k in range(0, b["s"].size, 5):
        f.write(f"{k / 252:.4f},{100 * b['honest'][k]:.4f},{100 * b['cheat'][k]:.4f},{100 * b['cov'][k]:.4f}\n")

with open(OUT / "gbm.csv", "w") as f:
    f.write("t,mean,mean_th,median,median_th,p10,p90\n")
    for row in gbm_quantiles():
        f.write(",".join(f"{x:.4f}" for x in row) + "\n")
