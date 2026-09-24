"""Chart data for Book 4, Chapter 2 (deterministic, seeded)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_brownian import envelope_paths, qv_table, reflection_example, stop_table

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

w = envelope_paths()
t = np.linspace(0, 1, w.shape[1])
with open(OUT / "paths.csv", "w") as f:
    f.write("t," + ",".join(f"w{i}" for i in range(w.shape[0])) + ",up,dn\n")
    for k in range(w.shape[1]):
        env = 2 * np.sqrt(t[k])
        f.write(f"{t[k]:.4f}," + ",".join(f"{x:.4f}" for x in w[:, k]) + f",{env:.4f},{-env:.4f}\n")

e = reflection_example()
with open(OUT / "reflect.csv", "w") as f:
    f.write("t,w,refl\n")
    for k in range(e["w"].size):
        f.write(f"{e['t'][k]:.4f},{e['w'][k]:.4f},{e['refl'][k]:.4f}\n")

with open(OUT / "stops.csv", "w") as f:
    f.write("dist,cont,daily,bgk,bridge\n")
    for row in stop_table():
        f.write(",".join(f"{x:.4f}" for x in row) + "\n")

with open(OUT / "qv.csv", "w") as f:
    f.write("n,qv,tv\n")
    for n, qv, tv in qv_table():
        f.write(f"{n},{qv:.5f},{tv:.4f}\n")
