"""Chart data for Book 5, Chapter 28 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_library import EXPIRIES, ONE_YEAR, SCENARIOS, STRIKES, T0, bucket_profile, crn_noise, scenario_grid

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

b = bucket_profile()
with open(OUT / "vega_expiry.csv", "w") as f:
    f.write("months,vega\n")
    for e in EXPIRIES:
        f.write(f"{round((e - T0).days / 30.4)},{b['by_expiry'][e] / 1000:.4f}\n")
with open(OUT / "vega_1y.csv", "w") as f:
    f.write("strike,vega\n")
    for k in STRIKES:
        f.write(f"{k:.0f},{b['by_node'][(ONE_YEAR, k)] / 1000:.4f}\n")

c = crn_noise()
with open(OUT / "crn.csv", "w") as f:
    f.write("seed,with,without\n")
    for i, (a, w) in enumerate(zip(c["with"], c["without"], strict=True)):
        f.write(f"{i + 1},{a / 1000:.4f},{w / 1000:.4f}\n")

g = scenario_grid()
with open(OUT / "scenarios.csv", "w") as f:
    f.write("i,pnl\n")
    for i, sc in enumerate(SCENARIOS):
        f.write(f"{i},{g[sc.name] / 1000:.3f}\n")
