"""Chart data for Book 5, Chapter 12 (deterministic)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_roughvol import (
    LAGS,
    PUBLISHED_H,
    TENORS,
    bergomi_match,
    log_vol_paths,
    pdv_shock,
    rough_kernel,
    skew_term,
    structure_curves,
    variance_curve,
    vix_smile,
    vol_paths,
)

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

sc = structure_curves(log_vol_paths())
with open(OUT / "structure.csv", "w") as f:
    f.write("lag,rough,ou,noisy\n")
    for i, lag in enumerate(LAGS):
        f.write(f"{lag}," + ",".join(f"{sc[k][i]:.6g}" for k in ("rough", "ou", "noisy")) + "\n")

with open(OUT / "published_h.csv", "w") as f:
    f.write("i,name,h\n")
    for i, (name, h) in enumerate(sorted(PUBLISHED_H.items(), key=lambda kv: kv[1])):
        f.write(f"{i},{name},{h:.3f}\n")

curve, rows = variance_curve()
with open(OUT / "pillars.csv", "w") as f:
    f.write("t,atm,vs\n")
    for r in rows:
        f.write(f"{r['t']:.4f},{100 * r['atm']:.4f},{100 * r['vs']:.4f}\n")
with open(OUT / "fwdvol.csv", "w") as f:
    f.write("t,fwd\n")
    ts = [0.0, *curve.times]
    for a, b in zip(ts[:-1], ts[1:], strict=True):
        v = 100 * math.sqrt(curve.xi(b))
        f.write(f"{a:.4f},{v:.4f}\n{b:.4f},{v:.4f}\n")

omega, k = bergomi_match()
with open(OUT / "kernel.csv", "w") as f:
    f.write("tau,rough,bergomi\n")
    for tau in np.exp(np.linspace(math.log(1 / 252), math.log(2.0), 60)):
        f.write(f"{tau:.5f},{rough_kernel(tau):.5f},{omega * math.exp(-k * tau):.5f}\n")

vp = vol_paths()
with open(OUT / "volpaths.csv", "w") as f:
    f.write("day,rough,bergomi\n")
    for i in range(len(vp["t"])):
        f.write(f"{i + 1},{100 * vp['rough'][i]:.3f},{100 * vp['bergomi'][i]:.3f}\n")

st = skew_term()
a, alpha = st["fits"]["market"]
with open(OUT / "skew.csv", "w") as f:
    f.write("t,market,rbergomi,heston,fit\n")
    for i, t in enumerate(TENORS):
        f.write(f"{t:.5f},{-st['market'][i]:.5f},{-st['rbergomi'][i]:.5f},{-st['heston'][i]:.5f},"
                f"{a * t ** alpha:.5f}\n")

down, up = pdv_shock(-0.04), pdv_shock(0.04)
with open(OUT / "pdv.csv", "w") as f:
    f.write("day,down,up\n")
    for i in range(len(down)):
        f.write(f"{i - 1},{100 * down[i]:.3f},{100 * up[i]:.3f}\n")

vs = vix_smile()
with open(OUT / "vix.csv", "w") as f:
    f.write("strike,vol\n")
    for m, v in zip(vs["strikes"], vs["vols"], strict=True):
        f.write(f"{100 * m:.0f},{100 * v:.3f}\n")
