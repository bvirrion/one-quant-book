"""Chart data for Book 11, chapter 6 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
from hf_toxicity import CAL_SEEDS, H, calibration, mh, run  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

hs = (0.5, 1, 2, 5, 10, 20, 30, 60)
num = {True: np.zeros(len(hs)), False: np.zeros(len(hs))}
den = {True: 0.0, False: 0.0}
for s in CAL_SEEDS:
    r: mh.Result = run(s)[0]
    m = r.markouts(hs)
    for cls in (True, False):
        k = r.extra["informed"] == cls
        num[cls] += r.fills["qty"][k] @ m[k]
        den[cls] += r.fills["qty"][k].sum()
with open(OUT / "classes.csv", "w") as f:
    f.write("h,informed,uninformed\n")
    for i, h in enumerate(hs):
        f.write(f"{h},{num[True][i] / den[True]:.3f},{num[False][i] / den[False]:.3f}\n")

c = calibration()
with open(OUT / "calibration.csv", "w") as f:
    f.write("group,pred,real,se\n")
    for k in range(len(c["pred"])):
        f.write(f"{k + 1},{c['pred'][k]:.3f},{c['real'][k]:.3f},{c['se'][k]:.3f}\n")
assert H == 10.0
