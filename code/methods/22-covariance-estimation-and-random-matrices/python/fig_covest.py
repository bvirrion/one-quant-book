"""Chart data for Book 4, Chapter 22 (simulations seeded)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_covest import bias_vs_q, evaluate, mp_curve, spectrum, spike

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

s = spectrum()
edges = np.linspace(0, 3, 31)
h = np.histogram(s["noise"], bins=edges)[0] / (s["noise"].size * np.diff(edges))
hf = np.histogram(s["factor"][s["factor"] < 3], bins=edges)[0] / (s["factor"].size * np.diff(edges))
with open(OUT / "mp_hist.csv", "w") as f:
    f.write("x,noise,factor\n")
    for i in range(h.size):
        f.write(f"{0.5 * (edges[i] + edges[i + 1]):.3f},{h[i]:.4f},{hf[i]:.4f}\n")
with open(OUT / "mp_curve.csv", "w") as f:
    f.write("x,density\n")
    for x, d in mp_curve():
        f.write(f"{x:.4f},{d:.4f}\n")

with open(OUT / "bias.csv", "w") as f:
    f.write("q,sim,theory\n")
    for q, sim, th in bias_vs_q():
        f.write(f"{q:.3f},{sim:.4f},{th:.4f}\n")

with open(OUT / "spike.csv", "w") as f:
    f.write("ell,sim,theory\n")
    for ell, sim, th in spike():
        f.write(f"{ell:.2f},{sim:.4f},{th:.4f}\n")

E = evaluate()
with open(OUT / "estimators.csv", "w") as f:
    f.write("k,name,pred,real\n")
    for k, name in enumerate(("sample", "lw_identity", "lw_constcorr", "nonlinear", "clipped", "pca_factor")):
        f.write(f"{k},{name},{100 * E[name]['pred']:.2f},{100 * E[name]['real']:.2f}\n")
