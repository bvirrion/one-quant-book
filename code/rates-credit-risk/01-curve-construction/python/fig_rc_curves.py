"""Chart data for Book 6, chapter 1 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rc_curves import (  # noqa: E402
    ECB_2026_09_22,
    ECB_SPOT_2026_09_22,
    forward_table,
    instruments,
    locality,
    off_pillar_buckets,
    svensson,
    svensson_forward,
)

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/rates-credit-risk/01-curve-construction"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "forwards.csv", "w") as f:
    f.write("t,lz,ff,cs,mc\n")
    for row in forward_table(step=0.05):
        f.write(",".join(f"{x:.4f}" for x in row) + "\n")

with open(OUT / "locality.csv", "w") as f:
    f.write("t,lz,ff,cs,mc\n")
    for row in locality("7Y", step=0.05):
        f.write(",".join(f"{x:.4f}" for x in row) + "\n")

labels = [i.label for i in instruments()]
b = off_pillar_buckets(8)
keep = [k for k, lab in enumerate(labels) if lab in ("3Y", "4Y", "5Y", "7Y", "10Y", "12Y", "15Y")]
with open(OUT / "buckets8.csv", "w") as f:
    f.write("i,tenor,ff,cs,mc\n")
    for j, k in enumerate(keep):
        vals = [round(b[kd][k] / 1000, 3) + 0.0 for kd in ("flat_forward", "cubic_zero", "monotone_convex")]
        f.write(f"{j},{labels[k]}," + ",".join(f"{v:.3f}" for v in vals) + "\n")

with open(OUT / "svensson.csv", "w") as f:
    f.write("t,zero,fwd\n")
    for i in range(1, 301):
        t = i / 10
        f.write(f"{t:.1f},{svensson(t, **ECB_2026_09_22):.4f},{svensson_forward(t, **ECB_2026_09_22):.4f}\n")
with open(OUT / "ecbpoints.csv", "w") as f:
    f.write("t,zero\n")
    for t, z in ECB_SPOT_2026_09_22.items():
        f.write(f"{t},{z:.4f}\n")
