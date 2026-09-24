"""Chart data for Book 5, Chapter 24 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_calib import REGS, daily, profile, scan, transform_study

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

ts = transform_study()
with open(OUT / "cos.csv", "w") as f:
    f.write("n,err\n")
    for n, e in ts["cos"].items():
        f.write(f"{n},{e:.3e}\n")
with open(OUT / "fft.csv", "w") as f:
    f.write("n,err\n")
    for n, e in ts["fft"].items():
        f.write(f"{n},{e:.3e}\n")

with open(OUT / "profile.csv", "w") as f:
    f.write("eta,rmse,kappa\n")
    for e, r in profile().items():
        f.write(f"{e:.2f},{100 * r['rmse']:.4f},{r['kappa']:.4f}\n")

chosen = scan()["chosen"]
free, reg = daily(0.0), daily(chosen)
with open(OUT / "daily.csv", "w") as f:
    f.write("day,eta_free,eta_reg,kappa_free,kappa_reg,conv_free,conv_reg\n")
    for i in range(len(free["eta"])):
        f.write(f"{i + 1},{free['eta'][i]:.4f},{reg['eta'][i]:.4f},{free['kappa'][i]:.4f},{reg['kappa'][i]:.4f},"
                f"{100 * free['conv'][i]:.4f},{100 * reg['conv'][i]:.4f}\n")

s = scan()
with open(OUT / "scan.csv", "w") as f:
    f.write("reg,max_d_eta,d_rmse\n")
    for r in REGS[1:]:
        f.write(f"{r:.0e},{s['rows'][r]['max_d_eta']:.4f},{100 * s['rows'][r]['d_rmse']:.4f}\n")
