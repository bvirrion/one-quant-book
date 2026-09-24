"""Chart data for Chapter 31 (deterministic)."""
import pathlib
import sys
from dataclasses import replace

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from withdrawal import Params, depth_needed, run, trough

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/31-stress-case-studies"
OUT.mkdir(parents=True, exist_ok=True)

base = Params()
cases = {"feedback": base, "none": replace(base, withdrawal=0.0, churn=0.0), "pause": replace(base, pause_at=0.05)}
paths = {k: run(v, 75_000) for k, v in cases.items()}
with open(OUT / "paths.csv", "w") as f:
    f.write("minute,feedback,none,pause,depth_pct,sell_k\n")
    for i in range(60):
        f.write(f"{i + 1}," + ",".join(f"{(paths[k][i][0] - 1) * 100:.3f}" for k in ("feedback", "none", "pause"))
                + f",{paths['feedback'][i][1] / base.depth0 * 100:.2f},{paths['feedback'][i][2] / 1e3:.3f}\n")

with open(OUT / "depth_needed.csv", "w") as f:
    f.write("max_fall_pct,depth_k\n")
    for m in (2, 3, 4, 5, 6, 8):
        f.write(f"{m},{depth_needed(base, 75_000, m / 100) / 1e3:.1f}\n")

with open(OUT / "halts.csv", "w") as f:              # published counts, 24 August 2015
    f.write("group,halts,securities\n")
    f.write("exchange-traded products,1058,327\nother securities,220,144\n")
print({k: round(trough(v) * 100, 2) for k, v in paths.items()})
