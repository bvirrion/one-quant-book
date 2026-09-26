"""Chart data for Book 10, chapter 19 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_tca import study  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

s = study()
with open(OUT / "attribution.csv", "w") as f:
    f.write("i,part,patient,urgent\n")
    for i, k in enumerate(("delay", "spread", "impact", "timing", "opportunity", "fees", "total")):
        f.write(f"{i},{k},{s['patient'][k]:.3f},{s['urgent'][k]:.3f}\n")
d = s["diff"]
with open(OUT / "estimates.csv", "w") as f:
    f.write("y,est,lo,hi\n")
    t, se = s["true"]
    f.write(f"3,{d['raw']:.3f},{d['raw'] - 1.96 * d['raw_se']:.3f},{d['raw'] + 1.96 * d['raw_se']:.3f}\n")
    f.write(f"2,{d['adj']:.3f},{d['lo']:.3f},{d['hi']:.3f}\n")
    f.write(f"1,{t:.3f},{t - 1.96 * se:.3f},{t + 1.96 * se:.3f}\n")
with open(OUT / "calibration.csv", "w") as f:
    f.write("pred,real,se\n")
    for p, r, e in s["calibration"]:
        f.write(f"{p:.3f},{r:.3f},{e:.3f}\n")
