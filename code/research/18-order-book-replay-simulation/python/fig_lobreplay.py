"""Chart data for Book 7, chapter 18 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_lobreplay import LATENCIES, touch_grid  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

g = touch_grid()
with open(OUT / "latency.csv", "w") as f:
    cols = [f"{m}_{v}" for m in ("front", "fifo", "prob") for v in ("pnl", "lots", "markout")]
    f.write("k,latency," + ",".join(cols) + "\n")
    for k, lat in enumerate(LATENCIES):
        vals = [g[(m, lat)][v] for m in ("front", "fifo", "prob") for v in ("pnl", "lots", "markout")]
        f.write(f"{k},{lat}," + ",".join(f"{x:.4f}" for x in vals) + "\n")
