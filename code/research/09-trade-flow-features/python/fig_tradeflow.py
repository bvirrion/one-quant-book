"""Chart data for Book 7, chapter 9 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_tradeflow import markout_series, memory, signing, vpin_series  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

sg = signing()
with open(OUT / "signing.csv", "w") as f:
    f.write("k,rule,accuracy\n")
    for k, (name, v) in enumerate(sg.items()):
        f.write(f"{k},{name.replace(',', ';')},{v:.4f}\n")

acf, _ = memory((1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 70, 100))
with open(OUT / "signacf.csv", "w") as f:
    f.write("lag,acf\n")
    for k, v in acf.items():
        f.write(f"{k},{max(v, 1e-4):.5f}\n")

tv, v, _ = vpin_series()
with open(OUT / "vpin.csv", "w") as f:
    f.write("minute,vpin\n")
    for t, x in zip(tv, v, strict=True):
        if x == x:
            f.write(f"{t / 60:.3f},{x:.4f}\n")
tm, m, _ = markout_series()
with open(OUT / "markout.csv", "w") as f:
    f.write("minute,markout\n")
    for t, x in zip(tm, m, strict=True):
        f.write(f"{t / 60:.3f},{x:.4f}\n")
