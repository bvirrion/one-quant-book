"""Chart data for Book 7, chapter 21 (deterministic)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_abtest import TARGET, calibration, peeking, simulated_power, stopping, world  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "abtest"))
from firm_abtest import power  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

w = world()
cal = calibration()
se60 = {"raw": cal["difference in means"][2], "cuped": cal["CUPED (pre-trade + market)"][2],
        "day": cal["randomised by day"][2]}
with open(OUT / "power.csv", "w") as f:
    f.write("days,raw,cuped,day\n")
    for d in range(2, 121, 2):
        f.write(f"{d}," + ",".join(f"{power(TARGET, se60[k] * math.sqrt(60 / d)):.4f}" for k in se60) + "\n")
with open(OUT / "power_sim.csv", "w") as f:
    f.write("days,raw,cuped\n")
    for d in (20, 40, 60, 80, 100):
        raw, cup = simulated_power(d)
        f.write(f"{d},{raw:.3f},{cup:.3f}\n")

sdc = w["sd"] * math.sqrt(1 - w["r2_both"])
pk = peeking(sdc, horizons=tuple(range(1, 121)))
with open(OUT / "peeking.csv", "w") as f:
    f.write("days,naive,msprt\n")
    for h, (a, b) in pk.items():
        f.write(f"{h},{a:.4f},{b:.4f}\n")
st = stopping(sdc)
with open(OUT / "stopping.csv", "w") as f:
    f.write("days,share\n")
    for d in range(1, 121):
        f.write(f"{d},{np.mean(st <= d):.4f}\n")
