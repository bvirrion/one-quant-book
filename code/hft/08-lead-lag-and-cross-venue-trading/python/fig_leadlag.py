"""Chart data for Book 11, chapter 8 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from hf_leadlag import GRID_LAGS, SEEDS, edge_curve, estimate, table  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/hft" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

e = estimate(0.5, SEEDS[0])
with open(OUT / "ccf.csv", "w") as f:
    f.write("lag,ccf\n")
    for lag, c in zip(GRID_LAGS, e["ccf"], strict=True):
        f.write(f"{lag},{c:.4f}\n")

with open(OUT / "edge.csv", "w") as f:
    f.write("latency_ms,edge,se\n")
    for lat, r in edge_curve().items():
        f.write(f"{1000 * lat:g},{r['edge']:.3f},{r['se']:.3f}\n")

with open(OUT / "shares.csv", "w") as f:
    f.write("lag,is_low,is_high,component\n")
    for lag, r in table().items():
        f.write(f"{lag},{r['is_low']:.3f},{r['is_high']:.3f},{r['component']:.3f}\n")
