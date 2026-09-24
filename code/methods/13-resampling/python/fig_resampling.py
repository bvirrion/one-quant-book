"""Chart data for Book 4, Chapter 13 (deterministic, seeded)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_resampling import coverage, problem, reality_check, sampling_sd, se_by_block

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

P = problem()
edges = np.linspace(-1.5, 4.0, 45)
w = np.diff(edges)
h_iid = np.histogram(P["iid_draws"], bins=edges)[0] / (P["iid_draws"].size * w)
h_sb = np.histogram(P["stationary_draws"], bins=edges)[0] / (P["stationary_draws"].size * w)
with open(OUT / "dist.csv", "w") as f:
    f.write("x,iid,stationary\n")
    for i in range(w.size):
        f.write(f"{0.5 * (edges[i] + edges[i + 1]):.4f},{h_iid[i]:.4f},{h_sb[i]:.4f}\n")

truth = sampling_sd()
with open(OUT / "blocks.csv", "w") as f:
    f.write("block,se,truth\n")
    for b, se in se_by_block():
        f.write(f"{b},{se:.4f},{truth:.4f}\n")

c_auto = coverage()
c_40 = coverage(block=40)
with open(OUT / "coverage.csv", "w") as f:
    f.write("k,method,coverage\n")
    f.write(f"0,iid,{c_auto['pct']['iid']:.2f}\n1,moving block,{c_auto['pct']['block']:.2f}\n")
    f.write(f"2,stationary,{c_auto['pct']['stationary']:.2f}\n3,stationary 40,{c_40['pct']['stationary']:.2f}\n")

R = reality_check()
mx = np.sort(R["max_draws"])
sys.path.insert(0, str(HERE.parents[2] / "12-testing-and-multiple-testing" / "python"))
from qm_testing import correlated_max_draws  # noqa: E402

gx = np.sort(correlated_max_draws())
with open(OUT / "rc.csv", "w") as f:
    f.write("c,bootstrap,gaussian\n")
    for c in np.linspace(0, 4, 81):
        pb = 1 - np.searchsorted(mx, c, side="left") / mx.size
        pg = 1 - np.searchsorted(gx, c, side="left") / gx.size
        f.write(f"{c:.2f},{max(pb, 1e-4):.5f},{max(pg, 1e-4):.5f}\n")
