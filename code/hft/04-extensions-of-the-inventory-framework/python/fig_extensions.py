"""Chart data for Book 11, chapter 4 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
from hf_extensions import PHIS2, QMAX, A, K, cross_skew, frontier2, mm  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

qs = np.arange(-QMAX, QMAX + 1)
rows = {}
for phi in (0.5, 5.0):
    rows[phi] = (mm.stationary(A, K, phi, QMAX)[0], mm.asymptotic(A, K, phi, qs)[0])
with open(OUT / "closed.csv", "w") as f:
    f.write("q,exact05,closed05,exact5,closed5\n")
    for i, q in enumerate(qs):
        if abs(q) <= 8:
            f.write(f"{q}," + ",".join(f"{rows[p][j][i]:.4f}" for p in (0.5, 5.0) for j in (0, 1)) + "\n")

fr = frontier2()
with open(OUT / "frontier2.csv", "w") as f:
    f.write("phi,risk_joint,mean_joint,risk_sep,mean_sep\n")
    for p in PHIS2:
        j, s = fr["joint"][p], fr["separate"][p]
        f.write(f"{p},{j['risk']:.3f},{j['mean']:.2f},{s['risk']:.3f},{s['mean']:.2f}\n")

c = cross_skew()
with open(OUT / "cross.csv", "w") as f:
    f.write("q1,short4,flat,long4\n")
    for i, q in enumerate(c["q1"]):
        f.write(f"{q},{c[-4][i]:.4f},{c[0][i]:.4f},{c[4][i]:.4f}\n")
