"""Chart data for Chapter 17 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from wrappers import WRAPPERS, DrTerms, breakdown, dr_band_bp, total

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/17-delta-one-instruments"
OUT.mkdir(parents=True, exist_ok=True)

for tag, financed in (("cash", 0.0), ("leveraged", 1.0)):
    with open(OUT / f"stack_{tag}.csv", "w") as f:
        f.write("wrapper,trading,tax,running,funding,dividends,total\n")
        for w in WRAPPERS:
            b = breakdown(w, 1.0, 200.0, financed)
            f.write(f"{w.name}," + ",".join(f"{v:.1f}" for v in b.values()) + f",{sum(b.values()):.1f}\n")

with open(OUT / "horizon.csv", "w") as f:
    f.write("years," + ",".join(w.name for w in WRAPPERS) + "\n")
    for k in range(1, 61):
        y = k / 12
        f.write(f"{y:.4f}," + ",".join(f"{total(w, y, 200.0, 0.0) / y:.2f}" for w in WRAPPERS) + "\n")

with open(OUT / "band.csv", "w") as f:
    f.write("receipt_price,lower_bp,upper_bp\n")
    for p in (5, 10, 15, 20, 25, 40, 60, 80, 100):
        lo, hi = dr_band_bp(p / 1.25 / 4.0, 1.25, DrTerms(4.0, 0.05, 0.05, 0.0, 6.0))
        f.write(f"{p},{lo:.1f},{hi:.1f}\n")
