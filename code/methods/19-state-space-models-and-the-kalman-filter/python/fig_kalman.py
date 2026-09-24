"""Chart data for Book 4, Chapter 19 (FRED/EIA oil prices and ECB rates in data/methods; simulations seeded)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_kalman import compare, em_path, eurusd_returns, gain_curve, load, sv_filter, sv_grid, tradeoff

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[4]
OUT = ROOT / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

d = load()
c = compare()
with open(OUT / "ratio.csv", "w") as f:
    f.write("year,kalman,lo,hi,smooth,roll\n")
    for t in range(d["dates"].size):
        if d["dates"][t] < "2019-01-01" or t % 2:
            continue
        y, m, dd = (int(v) for v in d["dates"][t].split("-"))
        k, s = c["k_filt"][t], c["k_sd"][t]
        f.write(f"{y + (m - 1) / 12 + (dd - 1) / 365:.4f},{k:.4f},{k - 2 * s:.4f},{k + 2 * s:.4f},"
                f"{c['k_smooth'][t]:.4f},"
                f"{c['roll'][t]:.4f}\n")

with open(OUT / "tradeoff.csv", "w") as f:
    f.write("mult,relvar,halfdays\n")
    for m, v, h in tradeoff():
        f.write(f"{m},{v:.4f},{h:.2f}\n")

e = em_path(40)
with open(OUT / "em.csv", "w") as f:
    f.write("iter,loglik,mle\n")
    for i, ll in enumerate(e["lls"]):
        f.write(f"{i + 1},{ll:.3f},{c['loglik']:.3f}\n")

with open(OUT / "gain.csv", "w") as f:
    f.write("q,gain\n")
    for q, g in gain_curve(np.geomspace(1e-4, 100, 49)):
        f.write(f"{q:.6g},{g:.5f}\n")

g = sv_grid()
dates, r = eurusd_returns()
sv = sv_filter(r, g["phi"], g["sigma"])
sys.path.insert(0, str(ROOT / "code" / "firm" / "volfcst"))
from firm_volfcst import garch_fit  # noqa: E402

rr = 100 * np.diff(np.log(np.genfromtxt(ROOT / "data/methods/eur_fx_ecb_1999_2026.csv", delimiter=",", names=True,
                                         dtype=None, encoding=None)["usd_per_eur"].astype(float)))
gv = np.sqrt(garch_fit(rr, "t")["h"][:-1])[-r.size:]
with open(OUT / "sv.csv", "w") as f:
    f.write("year,sv,garch,ess\n")
    for t in range(r.size):
        y, m, dd = (int(v) for v in dates[t].split("-"))
        f.write(f"{y + (m - 1) / 12 + (dd - 1) / 365:.4f},{math.exp(sv['logvar_mean'][t] / 2):.4f},{gv[t]:.4f},"
                f"{sv['ess'][t]:.0f}\n")
