"""Chart data for Book 5, Chapter 11 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_sabr import backbone, delta_curves, smiles_at_forwards, wing_density

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

fs = np.linspace(0.02, 0.04, 41)
bbs = {b: backbone(b, fs) for b in (0.0, 0.5, 1.0)}
with open(OUT / "backbone.csv", "w") as f:
    f.write("fwd,b0,b05,b1\n")
    for i, x in enumerate(fs):
        f.write(f"{100 * x:.3f}," + ",".join(f"{100 * bbs[b][i][1]:.4f}" for b in (0.0, 0.5, 1.0)) + "\n")

sm = smiles_at_forwards()
with open(OUT / "smiles.csv", "w") as f:
    f.write("k,f025,f03,f035\n")
    for i, (k, _) in enumerate(sm[0.03]):
        f.write(f"{100 * k:.3f}," + ",".join(f"{100 * sm[x][i][1]:.4f}" for x in (0.025, 0.03, 0.035)) + "\n")

ks, dens = wing_density()
with open(OUT / "density.csv", "w") as f:
    f.write("k,density\n")
    for k, d in zip(ks, dens, strict=True):
        f.write(f"{100 * k:.4f},{d:.4f}\n")

with open(OUT / "deltas.csv", "w") as f:
    f.write("k,black,hagan,bartlett\n")
    for k, d in delta_curves():
        f.write(f"{100 * k:.3f},{d['black']:.5f},{d['hagan']:.5f},{d['bartlett']:.5f}\n")

from dv_sabr import equity_fit  # noqa: E402

e = equity_fit()
with open(OUT / "equity_fit.csv", "w") as f:
    f.write("strike,market,sabr\n")
    for k, m, s in zip(e["ks"], e["market"], e["fitted"], strict=True):
        f.write(f"{k:.1f},{100 * m:.4f},{100 * s:.4f}\n")
