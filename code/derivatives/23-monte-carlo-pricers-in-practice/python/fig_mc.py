"""Chart data for Book 5, Chapter 23 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_mc import adjoint, bounds, heston_bias, put_bias, qmc_study

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

b = bounds()
with open(OUT / "bounds.csv", "w") as f:
    f.write("i,label,lower,lower_se,upper,upper_se\n")
    for i, name in enumerate(("full", "small")):
        lo, up = b[name]["lower"], b[name]["upper"]
        f.write(f"{i},{name},{lo[0]:.4f},{lo[1]:.4f},{up[0]:.4f},{up[1]:.4f}\n")
pb = put_bias()
with open(OUT / "inner_bias.csv", "w") as f:
    f.write("inner,upper,se,tree\n")
    for n, (u, se) in pb["upper"].items():
        f.write(f"{n},{u:.4f},{se:.4f},{pb['tree']:.4f}\n")

a = adjoint()
with open(OUT / "bucket_vega.csv", "w") as f:
    f.write("month,vega\n")
    for i, v in enumerate(a["bucket_vega"]):
        f.write(f"{i + 1},{v:.4f}\n")

h = heston_bias()
with open(OUT / "heston_bias.csv", "w") as f:
    f.write("steps,euler,qe,se\n")
    for steps, r in h["rows"].items():
        f.write(f"{steps},{abs(r['euler']):.5f},{max(abs(r['qe']), 1e-4):.5f},{r['se']:.5f}\n")

q = qmc_study()
with open(OUT / "qmc.csv", "w") as f:
    f.write("n,mc,halton,bridge\n")
    for n, r in q.items():
        f.write(f"{n},{r['mc']:.5f},{r['halton']:.5f},{r['bridge']:.5f}\n")
