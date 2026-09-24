"""Chart data for Book 6, chapter 7 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rc_shortrate import calibrations, fit_table, g2_table, vol_term_structure  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk" / pathlib.Path(__file__).parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "voltermstructure.csv", "w") as f:
    f.write("t,k0,k3,k10\n")
    for row in vol_term_structure():
        f.write(",".join(f"{x:.4f}" for x in row) + "\n")

with open(OUT / "fit.csv", "w") as f:
    f.write("e,market,constant,piecewise\n")
    for row in fit_table():
        f.write(",".join(f"{x:.3f}" for x in row) + "\n")

pw = calibrations()["piecewise"]
with open(OUT / "sigma.csv", "w") as f:
    f.write("t,sigma\n")
    edges = [0.0] + pw.knots + [10.0]
    for i, s in enumerate(pw.sigmas):
        f.write(f"{edges[i]:.1f},{1e4 * s:.3f}\n")
    f.write(f"{edges[-1]:.1f},{1e4 * pw.sigmas[-1]:.3f}\n")

with open(OUT / "g2.csv", "w") as f:
    f.write("t,g2,one\n")
    for t, c in g2_table():
        f.write(f"{t:.1f},{c:.4f},1.0\n")
