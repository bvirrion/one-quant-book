"""Chart data for Book 8, chapter 15 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_options import HORIZONS, ic  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "ic.csv", "w") as f:
    f.write("h,skew,spread,os,skew_ev,spread_ev,os_ev\n")
    for h in HORIZONS:
        vals = [ic(n, h) for n in ("skew", "spread", "os")] + [ic(n, h, True) for n in ("skew", "spread", "os")]
        f.write(f"{h}," + ",".join(f"{v:.4f}" for v in vals) + "\n")
