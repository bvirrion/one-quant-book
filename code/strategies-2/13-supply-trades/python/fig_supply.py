"""Chart data for Book 9, chapter 13 (deterministic)."""
import csv
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_supply import DATA, market, results, supply_trade  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(DATA / "auctions_path.csv") as fh, open(OUT / "path.csv", "w") as f:
    f.write("day,bp\n")
    for row in csv.DictReader(fh):
        f.write(f"{row['day']},{float(row['mean_bp']):.3f}\n")

cfg, sim = market()
p = supply_trade(sim, cfg)["pnl"]
with open(OUT / "scatter.csv", "w") as f:
    f.write("size,pnl\n")
    for s, x in zip(sim["size"], p, strict=True):
        f.write(f"{s:.2f},{x:.2f}\n")
b = results()["slope_size"]
a = float(np.mean(p) - b * np.mean(sim["size"]))
with open(OUT / "fit.csv", "w") as f:
    f.write("size,fit\n")
    for s in (20.0, 45.0):
        f.write(f"{s:.1f},{a + b * s:.3f}\n")
