"""Chart data for Book 4, Chapter 17 (FRED DGS2/DGS10 in data/methods; simulations seeded)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_tsa import _ar1_paths, _ols_rho, acf, df_distribution, load, long_memory, problem

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

d = load()
s = d["spread"]
with open(OUT / "spread.csv", "w") as f:
    f.write("year,spread\n")
    for i in range(0, s.size, 5):
        y, m, dd = (int(v) for v in d["dates"][i].split("-"))
        f.write(f"{y + (m - 1) / 12 + (dd - 1) / 365:.4f},{s[i]:.1f}\n")

a_lev, a_chg = acf(s, 250), acf(np.diff(s), 250)
with open(OUT / "acf.csv", "w") as f:
    f.write("lag,levels,changes\n")
    for k in range(1, 251):
        f.write(f"{k},{a_lev[k]:.4f},{a_chg[k]:.4f}\n")

tau = df_distribution()
edges = np.linspace(-5, 3, 41)
h = np.histogram(tau, bins=edges)[0] / (tau.size * np.diff(edges))
with open(OUT / "df.csv", "w") as f:
    f.write("tau,density,normal\n")
    for i in range(h.size):
        c = 0.5 * (edges[i] + edges[i + 1])
        f.write(f"{c:.2f},{h[i]:.4f},{np.exp(-c * c / 2) / np.sqrt(2 * np.pi):.4f}\n")

P = problem()
rng_edges = np.linspace(0, 2000, 41)
r, _ = _ols_rho(_ar1_paths(P["rho_kendall"], P["n"], 4000, np.random.default_rng(3)))
hl = np.log(0.5) / np.log(np.clip(r, 1e-12, 1 - 1e-15))
hh = np.histogram(np.clip(hl, 0, 1999), bins=rng_edges)[0] / (hl.size * np.diff(rng_edges))
with open(OUT / "halflife.csv", "w") as f:
    f.write("days,density\n")
    for i in range(hh.size):
        f.write(f"{0.5 * (rng_edges[i] + rng_edges[i + 1]):.0f},{1000 * hh[i]:.4f}\n")

lm = long_memory()
theory = np.cumprod([(i - 1 + 0.3) / (i - 0.3) for i in range(1, 201)])
with open(OUT / "longmem.csv", "w") as f:
    f.write("lag,arfima,theory,ar1\n")
    for k in range(1, 201):
        f.write(f"{k},{max(lm['acf'][k], 1e-4):.5f},{theory[k - 1]:.5f},{max(lm['acf_ar1'][k], 1e-6):.6g}\n")
