"""Chart data for Book 2, Chapter 17 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from fixflow_demo import fixing_order, hedge_flow_grid, price_path

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

paths = {p: price_path(p) for p in (0.0, 0.5, 1.0)}
with open(OUT / "path.csv", "w") as f:
    f.write("t,p0,p50,p100\n")
    for i, (t, _) in enumerate(paths[0.0]):
        f.write(f"{t:.3f}," + ",".join(f"{paths[p][i][1]:.4f}" for p in (0.0, 0.5, 1.0)) + "\n")
with open(OUT / "pnl.csv", "w") as f:
    f.write("p,pnl,lo,hi\n")
    for k in range(11):
        r = fixing_order(k / 10)
        f.write(f"{k / 10:.1f},{r['pnl'] / 1e3:.3f},{(r['sim_mean'] - r['sim_sd']) / 1e3:.3f},"
                f"{(r['sim_mean'] + r['sim_sd']) / 1e3:.3f}\n")

with open(OUT / "hedgeflow.csv", "w") as f:
    f.write("ret,h25,h50,h75\n")
    for r, a, b, c in hedge_flow_grid():
        f.write(f"{r},{a:.1f},{b:.1f},{c:.1f}\n")
