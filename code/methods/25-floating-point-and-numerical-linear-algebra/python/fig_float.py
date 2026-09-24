"""Chart data for Book 4, Chapter 25 (simulations seeded)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_float import cg_demo, normal_equations, summation_errors, vancouver, variance_errors

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

v = vancouver()
with open(OUT / "vancouver.csv", "w") as f:
    f.write("day,truncated,exact\n")
    for k in range(0, v["path"].size, 4):
        f.write(f"{k},{v['path'][k]:.3f},{v['exact_path'][k]:.3f}\n")

with open(OUT / "summation.csv", "w") as f:
    f.write("n,naive,pairwise,neumaier\n")
    for n, a, b, c, _ in summation_errors():
        f.write(f"{n},{a:.3e},{b:.3e},{max(c, 1e-12):.3e}\n")

with open(OUT / "variance.csv", "w") as f:
    f.write("offset,textbook,twopass,welford\n")
    for c, a, b, w, _, _ in variance_errors():
        f.write(f"{c:.0e},{max(a, 1e-17):.3e},{max(b, 1e-17):.3e},{max(w, 1e-17):.3e}\n")

with open(OUT / "normal.csv", "w") as f:
    f.write("cond,normal,qr\n")
    for k, ne, qr, _ in normal_equations():
        f.write(f"{k:.0e},{ne:.3e},{qr:.3e}\n")

c = cg_demo()
with open(OUT / "cg.csv", "w") as f:
    f.write("iter,plain,pre\n")
    rp, rq = c["res_plain"], c["res_pre"]
    for k in sorted(set(range(0, len(rp), 10)) | {len(rq) - 1}):
        q = f"{rq[k] / rq[0]:.3e}" if k < len(rq) else "nan"      # the preconditioned run has stopped
        f.write(f"{k},{max(rp[k] / rp[0], 1e-9):.3e},{q}\n")
