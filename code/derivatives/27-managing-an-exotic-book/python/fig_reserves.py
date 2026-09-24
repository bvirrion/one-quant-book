"""Chart data for Book 5, Chapter 27 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_reserves import day_one_study, rho_curve, stress

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "rho.csv", "w") as f:
    f.write("rho,value\n")
    for rho, v in rho_curve():
        f.write(f"{rho:.2f},{v:.4f}\n")

s = day_one_study()
with open(OUT / "models.csv", "w") as f:
    f.write("i,model,value\n")
    for i, (name, v) in enumerate(s["r0"]["models"].items()):
        f.write(f"{i},{name},{-v:.4f}\n")

st = stress()
with open(OUT / "stress.csv", "w") as f:
    f.write("shock," + ",".join(f"v{round(100 * v):+d}" for v in st["vols"]) + "\n")
    for j, ds in enumerate(st["shocks"]):
        f.write(f"{round(100 * ds)}," + ",".join(f"{st['grid'][i][j]:.4f}" for i in range(len(st["vols"]))) + "\n")

with open(OUT / "release.csv", "w") as f:
    f.write("year,deferred,released\n")
    for t, bal, rel in s["schedule"]:
        f.write(f"{t:.0f},{bal:.4f},{rel:.4f}\n")
