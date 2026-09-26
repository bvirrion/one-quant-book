"""Chart data for Book 11, chapter 7 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from hf_alpha import calibration, ic_by_delay, ic_by_horizon  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

names = ("imbalance", "ofi", "flow", "lead", "own", "combined")
with open(OUT / "ic.csv", "w") as f:
    f.write("h," + ",".join(names) + "\n")
    for h, row in ic_by_horizon().items():
        f.write(f"{h}," + ",".join(f"{row[k]:.3f}" for k in names) + "\n")

c = calibration()
with open(OUT / "calibration.csv", "w") as f:
    f.write("group,pred,real\n")
    for k in range(len(c["pred"])):
        f.write(f"{k + 1},{c['pred'][k]:.3f},{c['real'][k]:.3f}\n")

with open(OUT / "delay.csv", "w") as f:
    f.write("k,ms,ic\n")
    for k, v in ic_by_delay().items():
        if k:
            f.write(f"{k},{v['ms']:.1f},{v['ic']:.3f}\n")
