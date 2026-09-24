"""Chart data for Book 5, Chapter 10 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_heston import BASE, STRIKES, Heston, atm_skew_term, calibration, implied_vols, market_quotes, market_vol, smile

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
b = BASE

rhos = {r: smile(Heston(b.v0, b.kappa, b.vbar, b.eta, r)) for r in (-0.9, -0.5, 0.0)}
etas = {e: smile(Heston(b.v0, b.kappa, b.vbar, e, b.rho)) for e in (0.3, 0.6, 0.9)}
with open(OUT / "params.csv", "w") as f:
    f.write("strike,rho_m09,rho_m05,rho_0,eta03,eta06,eta09\n")
    for i, k in enumerate(STRIKES):
        vals = [rhos[r][i] for r in (-0.9, -0.5, 0.0)] + [etas[e][i] for e in (0.3, 0.6, 0.9)]
        f.write(f"{k:.1f}," + ",".join(f"{100 * v:.4f}" for v in vals) + "\n")

tenors = np.array([0.05, 0.1, 0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4, 5])
with open(OUT / "term.csv", "w") as f:
    f.write("t,v0_002,v0_004,v0_008\n")
    for t in tenors:
        vals = [implied_vols(Heston(v0, b.kappa, b.vbar, b.eta, b.rho), 100.0, [100.0], t)[0]
                for v0 in (0.02, 0.04, 0.08)]
        f.write(f"{t:.2f}," + ",".join(f"{100 * v:.4f}" for v in vals) + "\n")

m, rmse, per = calibration()
q = market_quotes()
with open(OUT / "calib.csv", "w") as f:
    f.write("strike,mkt3m,mod3m,mkt2y,mod2y\n")
    ks = np.arange(80.0, 120.01, 1.0)
    m3, m2 = implied_vols(m, 100.0, ks, 0.25), implied_vols(m, 100.0, ks, 2.0)
    for i, k in enumerate(ks):
        f.write(f"{k:.0f},{100 * market_vol(k, 0.25):.4f},{100 * m3[i]:.4f},"
                f"{100 * market_vol(k, 2.0):.4f},{100 * m2[i]:.4f}\n")

with open(OUT / "skew_term.csv", "w") as f:
    f.write("t,heston,market\n")
    for t, hs, ms in atm_skew_term(m, [1 / 52, 2 / 52, 1 / 12, 2 / 12, 0.25, 0.5, 0.75, 1, 1.5, 2]):
        f.write(f"{t:.4f},{-hs:.4f},{-ms:.4f}\n")
