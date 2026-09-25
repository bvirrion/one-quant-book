"""Chart data for Book 9, chapter 24 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_flowmm import markout_curve, policy  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "markout.csv", "w") as f:
    f.write("horizon,uninformed,moderate,informed\n")
    for h, m in markout_curve().items():
        f.write(f"{h}," + ",".join(f"{x:.3f}" for x in m) + "\n")

with open(OUT / "skew.csv", "w") as f:
    f.write("skew,net,internalised,inventory\n")
    for k in range(9):
        r = policy("priced", round(0.025 * k, 3))
        f.write(f"{0.025 * k:.3f},{r['net'] / 1000:.2f},{100 * r['internalised']:.2f},{r['abs_inventory']:.3f}\n")
