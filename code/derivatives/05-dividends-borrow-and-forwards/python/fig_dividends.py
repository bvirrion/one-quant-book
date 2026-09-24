"""Chart data for Book 5, Chapter 5 (deterministic)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_dividends import CURVE, curve_from_chain, model_smiles

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

f2 = CURVE.forward(2.0)
q = CURVE.rate - math.log(f2 / CURVE.spot) / 2.0            # continuous yield with the same 2-year forward
with open(OUT / "forward_curve.csv", "w") as f:
    f.write("t,discrete,smooth\n")
    for i in range(0, 731):
        t = i / 365.0
        f.write(f"{t:.4f},{CURVE.forward(t):.4f},{CURVE.spot * math.exp((CURVE.rate - q) * t):.4f}\n")

with open(OUT / "model_smiles.csv", "w") as f:
    f.write("strike,escrowed,spot,adjusted\n")
    for k, a, b, c in model_smiles(range(70, 131, 5)):
        f.write(f"{k},{100 * a:.4f},{100 * b:.4f},{100 * c:.4f}\n")

with open(OUT / "carry_steps.csv", "w") as f:
    f.write("t,implied,true\n")
    for r in curve_from_chain():
        f.write(f"{r['t']:.2f},{r['carry_step']:.4f},{r['carry_step_true']:.4f}\n")
