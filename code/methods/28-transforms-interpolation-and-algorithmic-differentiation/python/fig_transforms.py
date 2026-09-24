"""Chart data for Book 4, chapter 28: figdata/methods/28-transforms-interpolation-and-algorithmic-differentiation/."""
import pathlib

from qm_transforms import cos_convergence, cost_curve, forward_curves

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata" / "methods" / \
    "28-transforms-interpolation-and-algorithmic-differentiation"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "cos.csv", "w") as f:
    f.write("N,bs,merton\n")
    for n, eb, em in cos_convergence():
        f.write(f"{n},{eb:.3e},{em:.3e}\n")

fc = forward_curves(step=0.05)
with open(OUT / "forwards.csv", "w") as f:
    f.write("t,linear,spline,monotone\n")
    for i, t in enumerate(fc["t"]):
        f.write(f"{t:.3f},{100 * fc['linear'][i]:.4f},{100 * fc['spline'][i]:.4f},{100 * fc['monotone'][i]:.4f}\n")
x, r = fc["pillars"]
with open(OUT / "pillars.csv", "w") as f:
    f.write("t,zero\n")
    for a, b in zip(x, r, strict=True):
        f.write(f"{a:.4f},{100 * b:.2f}\n")

with open(OUT / "adcost.csv", "w") as f:
    f.write("n,bump,forward,reverse\n")
    for n, b, fw, rv in cost_curve():
        f.write(f"{n},{b},{fw:.2f},{rv:.4f}\n")
