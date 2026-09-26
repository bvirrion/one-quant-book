"""Chart data for Book 10, chapter 17 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_place import threshold_curve, urgent_study  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "threshold.csv", "w") as f:
    f.write("seconds,cut,agree\n")
    for t, cut, agree in threshold_curve():
        if t > 20.0:
            break
        f.write(f"{t:.1f},{cut:.3f},{agree:.3f}\n")
u = urgent_study()
with open(OUT / "urgent.csv", "w") as f:
    f.write("mid,diff,se,n\n")
    for lo, hi, n, d, se in u["buckets"]:
        f.write(f"{(max(lo, -1) + min(hi, 1)) / 2:.3f},{d:.3f},{se:.3f},{n}\n")
