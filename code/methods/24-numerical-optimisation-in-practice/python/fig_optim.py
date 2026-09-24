"""Chart data for Book 4, Chapter 24 (simulations seeded)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_optim import daily, lasso_prox, multistart, rates, valley

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

r = rates()
with open(OUT / "rates.csv", "w") as f:
    f.write("iter,gd,nesterov,theory\n")
    for k in range(0, r["gd"].size, 2):
        f.write(f"{k},{max(r['gd'][k], 1e-12):.3e},{max(r['nesterov'][k], 1e-12):.3e},{r['theory_gd'][k]:.3e}\n")

d0, d1 = daily(0.0), daily(0.01)
with open(OUT / "daily.csv", "w") as f:
    f.write("day,free,penalised\n")
    for k in range(d0["P"].shape[0]):
        f.write(f"{k + 1},{d0['P'][k, 2]:.3f},{d1['P'][k, 2]:.3f}\n")

v = valley()
with open(OUT / "valley.csv", "w") as f:
    f.write("tau2,rmse\n")
    for t2, e in v["profile"]:
        f.write(f"{t2:.2f},{1000 * e:.3f}\n")

ends = multistart()
with open(OUT / "multistart.csv", "w") as f:
    f.write("tau_fast,tau_slow,rmse\n")
    for _a, t1, t2, e in ends:
        f.write(f"{min(t1, t2):.3f},{max(t1, t2):.3f},{1000 * e:.3f}\n")

lp = lasso_prox()
with open(OUT / "lasso.csv", "w") as f:
    f.write("iter,ista,fista\n")
    for k in range(0, 151):
        f.write(f"{k},{max(lp['ista'][k], 1e-10):.3e},{max(lp['fista'][k], 1e-10):.3e}\n")  # floor at 1e-10
