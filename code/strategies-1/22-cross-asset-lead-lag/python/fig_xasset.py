"""Chart data for Book 8, chapter 22 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_xasset import LAGS, daily, intraday  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

d = daily()
with open(OUT / "lagscan.csv", "w") as f:
    f.write("lag,link1,link2,link3\n")
    for k in range(10):
        f.write(f"{k + 1}," + ",".join(f"{p[k]:.3f}" for p in d["lag_t_pairs"]) + "\n")

i = intraday()
with open(OUT / "ccf.csv", "w") as f:
    f.write("lag,ccf\n")
    for L, c in zip(LAGS, i["ccf"], strict=True):
        f.write(f"{L},{c:.4f}\n")
