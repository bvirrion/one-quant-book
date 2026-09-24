"""Chart data for Book 4, Chapter 20 (FRED DGS2/DGS5/DGS10 in data/methods; simulations seeded)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_coint import cointegration, eg_vs_df, load, rolling_weights, var_analysis

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)


def year(s):
    y, m, d = (int(v) for v in s.split("-"))
    return y + (m - 1) / 12 + (d - 1) / 365


d = load()
c = cointegration()
fj, f121 = c["fly_j"] - c["fly_j"].mean(), c["fly_121"] / 2 - (c["fly_121"] / 2).mean()
with open(OUT / "yields.csv", "w") as f:
    f.write("year,y2,y5,y10,flyj,fly121\n")
    for t in range(0, d["dates"].size, 5):
        f.write(f"{year(d['dates'][t]):.4f},{d['Y'][t, 0]:.0f},{d['Y'][t, 1]:.0f},{d['Y'][t, 2]:.0f},"
                f"{fj[t]:.1f},{f121[t]:.1f}\n")

v = var_analysis()
cum = np.cumsum(v["irf"][:, :, 0], axis=0)
with open(OUT / "irf.csv", "w") as f:
    f.write("day,y2,y5,y10\n")
    for h in range(cum.shape[0]):
        f.write(f"{h},{cum[h, 0]:.3f},{cum[h, 1]:.3f},{cum[h, 2]:.3f}\n")

e = eg_vs_df()
edges = np.linspace(-6, 2, 41)
hd = np.histogram(e["df"], bins=edges)[0] / (e["df"].size * np.diff(edges))
he = np.histogram(e["eg"], bins=edges)[0] / (e["eg"].size * np.diff(edges))
with open(OUT / "egdf.csv", "w") as f:
    f.write("tau,df,eg\n")
    for i in range(hd.size):
        f.write(f"{0.5 * (edges[i] + edges[i + 1]):.2f},{hd[i]:.4f},{he[i]:.4f}\n")

with open(OUT / "rolling.csv", "w") as f:
    f.write("end,w2,w10,rank\n")
    for label, w2, w10, rank in rolling_weights():
        if abs(w2) < 1.5 and abs(w10) < 1.5:
            f.write(f"{int(label[-4:])},{w2:.4f},{w10:.4f},{rank}\n")
