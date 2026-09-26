"""Chart data for Book 10, chapter 13 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_cross import cross_study, fair, llob_scan  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

s = llob_scan()
with open(OUT / "scan.csv", "w") as f:
    f.write("q,peak\n")
    for q, p in zip(s["sizes"], s["peaks"], strict=True):
        f.write(f"{q},{p:.5f}\n")
fp = fair()
with open(OUT / "path.csv", "w") as f:
    f.write("t,p\n")
    for t, p in list(zip(fp["t"], fp["p"], strict=True))[::100]:
        f.write(f"{t:.2f},{p:.5f}\n")
c = cross_study()
with open(OUT / "costs.csv", "w") as f:
    f.write("k,joint,own,sequential\n")
    for k, name in enumerate(("same", "pair")):
        v = c[name]
        f.write(f"{k},{v['joint']:.3f},{v['own_estimate']:.3f},{v['sequential']:.3f}\n")
