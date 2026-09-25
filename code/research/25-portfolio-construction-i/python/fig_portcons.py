"""Chart data for Book 7, chapter 25 (deterministic)."""
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")                     # before numpy: small matrices, many solves
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_portcons import SETTINGS, YEAR, decomposition, run, summary  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "ir.csv", "w") as f:
    f.write("level,exante,realised,net\n")
    for k in range(len(SETTINGS)):
        s = summary(k)
        f.write(f"{k},{s['ir_ex_ante']:.4f},{s['ir_realised']:.4f},{s['ir_net']:.4f}\n")

with open(OUT / "decomp.csv", "w") as f:
    f.write("group,share\n")
    d = decomposition(6)
    for k in ("factor neutral", "name limits", "gross limit", "liquidity", "turnover limit"):
        f.write(f"{k},{d.get(k, 0.0):.4f}\n")

paths = {}
for k in (0, 1, 4, 6):
    net = np.concatenate([r["net"] for r in run(k)])
    scaled = net * 0.10 / (net.std(ddof=1) * math.sqrt(YEAR))            # every book at 10% annual volatility
    paths[k] = np.cumsum(scaled)
with open(OUT / "cum.csv", "w") as f:
    f.write("year,naive,dollar,gross,turnover\n")
    n = len(paths[0])
    for i in range(0, n, 5):
        f.write(f"{(i + 1) / YEAR:.3f}," + ",".join(f"{paths[k][i]:.4f}" for k in (0, 1, 4, 6)) + "\n")
