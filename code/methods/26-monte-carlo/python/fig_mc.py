"""Chart data for Book 4, chapter 26 (Monte Carlo): writes figdata/methods/26-monte-carlo/*.csv."""
import pathlib

from qm_mc import digital_is, error_vs_cost, mlmc_study, orders, points_2d

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "methods" / "26-monte-carlo"
OUT.mkdir(parents=True, exist_ok=True)

p = points_2d()
with open(OUT / "points.csv", "w") as f:
    f.write("px,py,sx,sy\n")
    for a, b in zip(p["prng"], p["sobol"], strict=True):
        f.write(f"{a[0]:.5f},{a[1]:.5f},{b[0]:.5f},{b[1]:.5f}\n")

with open(OUT / "cost.csv", "w") as f:
    f.write("n,plain,cv,rqmcinc,rqmcbridge,rqmccv\n")
    for row in error_vs_cost():
        f.write(",".join([str(row[0])] + [f"{v:.4e}" for v in row[1:]]) + "\n")

with open(OUT / "orders.csv", "w") as f:
    f.write("steps,h,euler,milstein,weak\n")
    for n, e, m, w in orders():
        f.write(f"{n},{1 / n:.6f},{e:.4e},{m:.4e},{w:.4e}\n")

with open(OUT / "mlmc.csv", "w") as f:
    f.write("eps,mlmc,standard,levels\n")
    for r in mlmc_study():
        f.write(f"{r['eps']},{r['cost']:.4e},{r['std_cost']:.4e},{r['L']}\n")

d = digital_is()
with open(OUT / "is.csv", "w") as f:
    f.write("theta,relse\n")
    for th, _, rel in d["rows"]:
        f.write(f"{th:.1f},{rel:.4e}\n")
