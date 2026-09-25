"""Chart data for Book 9, chapter 29 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_surveil import detectors, roc  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

r = roc()
names = [k for k in r if k != "fpr"]
with open(OUT / "roc.csv", "w") as f:
    f.write("fpr,otr,gap,cancel,both\n")
    for i, x in enumerate(r["fpr"]):
        f.write(f"{100 * x:.2f}," + ",".join(f"{100 * r[n][i]:.1f}" for n in names) + "\n")
d = detectors()["spoof"]
with open(OUT / "flagged.csv", "w") as f:
    f.write("k,type,otr,gap,cancel,both\n")
    for k, t in enumerate(("market maker", "quote refresher", "deep provider", "directional", "spoofer")):
        f.write(f"{k},{t}," + ",".join(f"{100 * d[n]['by_type'][k]:.1f}" for n in d) + "\n")
