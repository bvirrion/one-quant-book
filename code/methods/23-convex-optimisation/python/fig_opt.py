"""Chart data for Book 4, Chapter 23 (simulated market, seeded)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_opt import broken_correlation, constraint_costs, today, turnover_curve

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "turnover.csv", "w") as f:
    f.write("limit,utility,expret,dual\n")
    for L, u, er, d, _ in turnover_curve():
        f.write(f"{100 * L:.0f},{100 * u:.4f},{100 * er:.4f},{d:.5f}\n")

c = constraint_costs()
base = today()
with open(OUT / "costs.csv", "w") as f:
    f.write("k,name,relax\n")
    for k, name in enumerate(("dollar", "sector", "position", "gross", "turnover")):
        f.write(f"{k},{name},{100 * c[name]:.4f}\n")

with open(OUT / "ipm.csv", "w") as f:
    f.write("iter,dual,primal,mu\n")
    for it, rd, rp, mu in base["history"]:
        f.write(f"{it},{max(rd, 1e-9):.2e},{max(rp, 1e-9):.2e},{max(mu, 1e-9):.2e}\n")  # floor: BLAS noise below 1e-9

b = broken_correlation()
with open(OUT / "ncm.csv", "w") as f:
    f.write("rank,before,after\n")
    for i, (x, y) in enumerate(zip(b["eig_before"], b["eig_after"], strict=True)):
        f.write(f"{i + 1},{x:.4f},{max(y, 0.0):.4f}\n")
