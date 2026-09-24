"""Chart data for Book 5, Chapter 22 (deterministic: errors against work in node updates, not run time)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_fd import accuracy_study, barrier_alignment, gamma_profile, oscillation, reference

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

ref = reference()
with open(OUT / "oscillation.csv", "w") as f:
    f.write("n,crr,ref\n")
    for n, v in oscillation():
        f.write(f"{n},{v:.6f},{ref:.6f}\n")

a = accuracy_study()
with open(OUT / "work_crr.csv", "w") as f:
    f.write("work,err\n")
    for n in range(100, 3001, 100):
        err = max(abs(a["crr_err"][n]), abs(a["crr_err"][n + 1]))
        f.write(f"{n * (n + 1) / 2:.0f},{100 * err:.6f}\n")
with open(OUT / "work_tri.csv", "w") as f:
    f.write("work,err\n")
    for n, e in sorted(a["tri_err"].items()):
        f.write(f"{n * n:.0f},{100 * abs(e):.6f}\n")
with open(OUT / "work_fd.csv", "w") as f:
    f.write("work,err,raw\n")
    for m in sorted(a["fd_err"]):
        f.write(f"{m * (m + 1) + 2 * m:.0f},{100 * abs(a['fd_err'][m]):.6f},{100 * abs(a['raw_err'][m]):.6f}\n")

g = gamma_profile()
s, gc = g["cn"]
_, gr = g["rannacher"]
_, ge = g["exact"]
with open(OUT / "gamma.csv", "w") as f:
    f.write("s,cn,rannacher,exact\n")
    for i in np.where((s > 90) & (s < 110))[0]:
        f.write(f"{s[i]:.4f},{gc[i]:.6f},{gr[i]:.6f},{ge[i]:.6f}\n")

b = barrier_alignment()
with open(OUT / "barrier.csv", "w") as f:
    f.write("m,aligned,misaligned\n")
    for m in sorted(b["aligned"]):
        f.write(f"{m},{abs(b['aligned'][m]):.6f},{abs(b['misaligned'][m]):.6f}\n")

from dv_fd import exercise_boundary, tree_boundary  # noqa: E402

with open(OUT / "boundary_grid.csv", "w") as f:
    f.write("tau,s\n")
    for tau, s_star in exercise_boundary():
        f.write(f"{tau:.4f},{s_star:.4f}\n")
with open(OUT / "boundary_tree.csv", "w") as f:
    f.write("tau,s\n")
    for tau, s_star in tree_boundary()[::3]:
        f.write(f"{tau:.4f},{s_star:.4f}\n")
