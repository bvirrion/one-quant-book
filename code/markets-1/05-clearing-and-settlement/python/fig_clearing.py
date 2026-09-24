"""Chart data for Chapter 5 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from clearing_demo import Waterfall, initial_margin, netting_efficiency, random_trades

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/05-clearing-and-settlement"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "netting.csv", "w") as f:
    f.write("trades,eff_pct\n")
    for n in (10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000):
        e = np.mean([netting_efficiency(random_trades(n, 8, seed)) for seed in range(20)])
        f.write(f"{n},{e * 100:.2f}\n")

with open(OUT / "margin_vs_vol.csv", "w") as f:
    f.write("sigma_pct,t2,t1\n")
    for s in range(1, 16):
        f.write(f"{s},{initial_margin(100, s / 100, 2):.2f},{initial_margin(100, s / 100, 1):.2f}\n")

w = Waterfall(120, 30, 20, 400, 400)
with open(OUT / "waterfall.csv", "w") as f:
    f.write("loss,margin,own_fund,ccp,survivors,assess,uncovered\n")
    for loss in range(0, 1101, 10):
        a = list(w.allocate(loss).values())
        f.write(f"{loss}," + ",".join(f"{x:.0f}" for x in a) + "\n")
