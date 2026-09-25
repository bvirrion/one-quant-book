"""Chart data for Book 7, chapter 5 (deterministic): the French-library statistics (data/research/ff_*.csv) with the
same statistics of firm.synthmkt's market factor."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_stylised import acf, aggregated_kurtosis, correlation_asymmetry, eigen, french_table, market

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

h = french_table("hist")
with open(OUT / "hist.csv", "w") as f:
    f.write("z,freq,normal\n")
    n = h["count"].sum()
    for z, c, e in zip(h["z"], h["count"], h["normal"], strict=True):
        if c > 0 or e > 1e-6:
            f.write(f"{z:.2f},{c / n if c > 0 else 'nan'},{max(e / n, 1e-9):.6g}\n")

a = french_table("acf")
m = market().mkt
with open(OUT / "acf.csv", "w") as f:
    f.write("lag,abs,sq,r,synth_abs\n")
    for k in (1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 70, 100, 150, 200, 250):
        i = int(k) - 1
        f.write(f"{k},{a['abs'][i]:.4f},{a['sq'][i]:.4f},{a['r'][i]:.4f},{acf(np.abs(m), k):.4f}\n")

g = french_table("agg")
hz = (1, 5, 10, 21, 63)
sk = aggregated_kurtosis(m, hz)
with open(OUT / "agg.csv", "w") as f:
    f.write("horizon,french,synth\n")
    for k, s in zip(hz, sk, strict=True):
        f.write(f"{k},{g['kurtosis'][list(g['horizon']).index(k)]:.3f},{s:.3f}\n")

asym = french_table("asym")
with open(OUT / "asym.csv", "w") as f:
    f.write("threshold,down,up,synth_down,synth_up\n")
    for c, d, u in zip(asym["threshold"], asym["down"], asym["up"], strict=True):
        sd, su, _ = correlation_asymmetry(c)
        f.write(f"{c:.2f},{d:.4f},{u:.4f},{sd:.4f},{su:.4f}\n")

ev, hi, shape = eigen()
with open(OUT / "eigen.csv", "w") as f:
    f.write("rank,eigenvalue\n")
    for i, v in enumerate(ev[:40], start=1):
        f.write(f"{i},{v:.4f}\n")
print("MP edge", round(hi, 3), "shape", shape, "above", int((ev > hi).sum()), "top", np.round(ev[:3], 2))
