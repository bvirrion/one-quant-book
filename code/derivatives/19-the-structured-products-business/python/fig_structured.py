"""Chart data for Book 5, Chapter 19 (deterministic)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_structured import R, capped_note, decrement_example, participation_curve, vol_target_options, vt_sample_path

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "participation.csv", "w") as f:
    f.write("spread,participation\n")
    for s, p in participation_curve():
        f.write(f"{1e4 * s:.1f},{100 * p:.3f}\n")

cap = capped_note()["cap"]
with open(OUT / "payoffs.csv", "w") as f:
    f.write("perf,protected,capped\n")
    for x in np.linspace(0.5, 1.6, 111):
        prot = 100 + 70 * max(x - 1, 0)
        capd = 100 + 100 * min(max(x - 1, 0), cap - 1)
        f.write(f"{100 * x:.1f},{prot:.3f},{capd:.3f}\n")

raw, vt, ex = vt_sample_path()
with open(OUT / "vt_path.csv", "w") as f:
    f.write("day,raw,vt,exposure\n")
    for i in range(len(raw)):
        e = ex[i] if i < len(ex) else ex[-1]
        f.write(f"{i},{100 * raw[i]:.3f},{100 * vt[i]:.3f},{100 * e:.2f}\n")

v = vol_target_options()
with open(OUT / "vt_iv.csv", "w") as f:
    f.write("k,raw,vt\n")
    for k, a, b in zip((90, 100, 110), v["raw_iv"], v["vt_iv"], strict=True):
        f.write(f"{k},{100 * a:.3f},{100 * b:.3f}\n")

d = decrement_example()
with open(OUT / "decrement.csv", "w") as f:
    f.write("t,price_fwd,dec_fwd\n")
    for day in d["days"][::21]:
        t = day / 252
        f.write(f"{t:.3f},{100 * math.exp((R - 0.03) * t):.3f},{100 * d['dec_path'][day]:.3f}\n")
