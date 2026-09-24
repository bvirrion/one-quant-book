"""Chart data for Book 5, Chapter 2 (deterministic)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_binomial import REAL, american_premium_curve, error, terminal_law

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

for parity in ("even", "odd"):
    with open(OUT / f"conv_{parity}.csv", "w") as f:
        f.write("n,crr,jr\n")
        for n in range(10 if parity == "even" else 11, 201, 2):
            f.write(f"{n},{error(n, 'crr'):.6f},{error(n, 'jr'):.6f}\n")
with open(OUT / "conv_lr.csv", "w") as f:
    f.write("n,lr\n")
    for n in range(11, 201, 2):
        f.write(f"{n},{error(n, 'lr'):.6f}\n")
with open(OUT / "american.csv", "w") as f:
    f.write("spot,european,american,intrinsic\n")
    for s, eu, am in american_premium_curve([60 + 2 * i for i in range(41)]):
        f.write(f"{s:.0f},{eu:.4f},{am:.4f},{max(REAL['strike'] - s, 0.0):.4f}\n")
x, w = terminal_law(50)
width = 2 * REAL["vol"] * math.sqrt(REAL["t"] / 50)
m, sd = (REAL["r"] - 0.5 * REAL["vol"] ** 2) * REAL["t"], REAL["vol"] * math.sqrt(REAL["t"])
with open(OUT / "terminal.csv", "w") as f:
    f.write("x,tree,normal\n")
    for xi, wi in zip(x, w, strict=True):
        if abs(xi) <= 0.8:
            dens = math.exp(-0.5 * ((xi - m) / sd) ** 2) / (sd * math.sqrt(2 * math.pi))
            f.write(f"{xi:.5f},{wi / width:.5f},{dens:.5f}\n")
