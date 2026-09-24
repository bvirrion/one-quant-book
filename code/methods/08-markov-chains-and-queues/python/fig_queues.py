"""Chart data for Book 4, Chapter 8 (deterministic, seeded)."""
import functools
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_queues import GRID, LAM, MU_MKT, NU, depletion_cdf, fill_time_cdf, mm1_simulation, race

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "mm1.csv", "w") as f:
    f.write("rho,theory,sim,lamW\n")
    for i, rho in enumerate((0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9)):
        r = mm1_simulation(rho, seed=10 + i)
        f.write(f"{rho},{r['L_theory']:.4f},{r['L']:.4f},{r['lamW']:.4f}\n")


@functools.cache
def dep(n):
    return depletion_cdf(LAM, NU, n, GRID)


with open(OUT / "moveup.csv", "w") as f:
    f.write("bid,ask10,ask20,ask40\n")
    for b in range(5, 101, 5):
        f.write(f"{b}," + ",".join(f"{race(dep(a), dep(b), GRID):.4f}" for a in (10, 20, 40)) + "\n")

with open(OUT / "fill.csv", "w") as f:
    f.write("ahead,ask10,ask20,ask40\n")
    for k in range(0, 121, 5):
        fc = fill_time_cdf(k, NU, MU_MKT, GRID)
        f.write(f"{k}," + ",".join(f"{race(fc, dep(a), GRID):.4f}" for a in (10, 20, 40)) + "\n")
