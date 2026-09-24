"""Chart data for Chapter 15 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from index_recon import event_path, ranks, reconstitute, simulate_turnover

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/15-index-construction-and-rebalancing"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "turnover.csv", "w") as f:
    f.write("buffer,names,weight_pct\n")
    for b in (0, 10, 20, 30, 40, 60):
        res = [simulate_turnover(600, 200, b, 20, s) for s in range(20)]
        f.write(f"{b},{np.mean([r[0] for r in res]):.2f},{np.mean([r[1] for r in res]) * 100:.3f}\n")

rng = np.random.default_rng(15)
caps = np.exp(rng.normal(0.0, 1.5, 600))
member = ranks(caps) <= 200
old_rank = ranks(caps)
caps2 = caps * np.exp(rng.normal(0.0, 0.35, 600))
new_rank = ranks(caps2)
new = reconstitute(caps2, member, 200, 20)
with open(OUT / "band.csv", "w") as f:
    f.write("old_rank,new_rank,outcome\n")
    for i in range(600):
        if not (150 <= new_rank[i] <= 250):
            continue
        if member[i] and new[i]:
            o = "kept" if new_rank[i] > 200 else "stays"
        elif member[i]:
            o = "deleted"
        elif new[i]:
            o = "added"
        else:
            o = "blocked" if new_rank[i] <= 200 else "outside"
        f.write(f"{old_rank[i]},{new_rank[i]},{o}\n")

with open(OUT / "event.csv", "w") as f:
    f.write("day,then_pct,now_pct\n")
    then = event_path(15, 30, -5, 0.034, 0.04, 6.0)
    now = event_path(15, 30, -5, 0.001, 0.002, 3.0)
    for k, d in enumerate(range(-15, 31)):
        f.write(f"{d},{then[k] * 100:.3f},{now[k] * 100:.3f}\n")
