"""Chart data for One Quant Book 15, chapter 18 (deterministic: the seeded afternoon, seed 18)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_rtrisk import afternoon, approximation_error  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

r = afternoon()
with open(OUT / "exposure.csv", "w") as f:
    f.write("hour,spot,firm_m,desk_a_m,desk_b_m\n")
    for i, (t, s, fe, a, b) in enumerate(r["series"]):
        if i % 6 == 0:
            f.write(f"{t / 3600:.4f},{s:.2f},{fe / 1e6:.3f},{a / 1e6:.3f},{b / 1e6:.3f}\n")
with open(OUT / "approximation.csv", "w") as f:
    f.write("move_pct,approx_k,full_k,error_pct\n")
    for x, a, fu, e in approximation_error(r):
        f.write(f"{100 * x:.2f},{a / 1e3:.2f},{fu / 1e3:.2f},{100 * e:.4f}\n")
