"""Chart data for Book 4, Chapter 5 (deterministic, seeded)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_numeraire import convergence_table, expected_short_rate, forward_rate, girsanov_histogram

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

g = girsanov_histogram()
with open(OUT / "girsanov.csv", "w") as f:
    f.write("x,p,q\n")
    for m, p, q in zip(g["mids"], g["p"], g["q"], strict=True):
        f.write(f"{m:.3f},{p:.5f},{q:.5f}\n")

with open(OUT / "convergence.csv", "w") as f:
    f.write("n,q,qlo,qhi,fwd,flo,fhi\n")
    for n, qp, qs, fp, fs in convergence_table():
        f.write(f"{n},{1e4 * qp:.4f},{1e4 * (qp - 2 * qs):.4f},{1e4 * (qp + 2 * qs):.4f},"
                f"{1e4 * fp:.4f},{1e4 * (fp - 2 * fs):.4f},{1e4 * (fp + 2 * fs):.4f}\n")

with open(OUT / "convexity.csv", "w") as f:
    f.write("t,gap\n")
    for k in range(1, 61):
        t = 0.5 * k
        f.write(f"{t:.1f},{1e4 * (expected_short_rate(t) - forward_rate(t)):.4f}\n")

