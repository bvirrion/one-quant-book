"""Chart data for Book 5, Chapter 14 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_varswap import contributions, hedge_pnl, heston_terms, replication_payoff, vix_curve, vix_options

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

k, w = contributions()
with open(OUT / "contrib.csv", "w") as f:
    f.write("k,share\n")
    for a, b in zip(k, w, strict=True):
        if a <= 160:
            f.write(f"{a:.1f},{100 * b:.4f}\n")

s, logp, strip = replication_payoff()
with open(OUT / "replication.csv", "w") as f:
    f.write("s,log,strip\n")
    for a, b, c in zip(s, logp, strip, strict=True):
        f.write(f"{a:.2f},{b:.5f},{c:.5f}\n")

with open(OUT / "heston_terms.csv", "w") as f:
    f.write("t,var,vol,market\n")
    for r in heston_terms():
        f.write(f"{r['t']:.4f},{100 * r['var']:.4f},{100 * r['vol']:.4f},{100 * r['market_var']:.4f}\n")

with open(OUT / "vix_curve.csv", "w") as f:
    f.write("months,future,fwd\n")
    for r in vix_curve():
        f.write(f"{12 * r['t']:.0f},{100 * r['future']:.4f},{100 * r['fwd']:.4f}\n")

vo = vix_options()
with open(OUT / "vix_smile.csv", "w") as f:
    f.write("strike,vol\n")
    for a, b in zip(vo["rel"], vo["vols"], strict=True):
        f.write(f"{100 * a:.0f},{100 * b:.3f}\n")

h = hedge_pnl()
with open(OUT / "hedge_tail.csv", "w") as f:
    f.write("loss,diffusion,jumps\n")
    for x in np.linspace(0.0, 3.0, 61):
        d, j = float(np.mean(h["diffusion"] < -x)), float(np.mean(h["jumps"] < -x))
        f.write(f"{x:.2f}," + (f"{d:.6f}" if d > 0 else "nan") + "," + (f"{j:.6f}" if j > 0 else "nan") + "\n")
