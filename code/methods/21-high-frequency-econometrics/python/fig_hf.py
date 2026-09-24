"""Chart data for Book 4, Chapter 21 (simulated market, seeded)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_hf import epps, estimators, mse_by_interval, signature

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

S = signature()
with open(OUT / "signature.csv", "w") as f:
    f.write("seconds,trade,mid,efficient\n")
    for s, (a, b, c) in S.items():
        f.write(f"{s},{100 * a:.2f},{100 * b:.2f},{100 * c:.2f}\n")

M = mse_by_interval()
with open(OUT / "mse.csv", "w") as f:
    f.write("seconds,rmse\n")
    for s, e in M.items():
        f.write(f"{s},{e:.4f}\n")

E = estimators()
with open(OUT / "estimators.csv", "w") as f:
    f.write("k,name,vol,sd\n")
    for k, name in enumerate(("rv300", "tsrv", "rv_opt", "preavg", "kernel")):
        f.write(f"{k},{name},{100 * E[name]['vol']:.2f},{100 * E[name]['sd_rel']:.1f}\n")

P = epps()
with open(OUT / "epps.csv", "w") as f:
    f.write("seconds,corr,hy,truth\n")
    for s, c in P["corr"].items():
        f.write(f"{s},{c:.4f},{P['hy']:.4f},{P['rho']:.2f}\n")
