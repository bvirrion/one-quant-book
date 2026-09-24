"""Chart data for Chapter 6 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from financing_demo import margin_call_price, return_on_equity, spiral

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/06-financing"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "roe.csv", "w") as f:
    f.write("asset_ret_pct,l1,l3,l8\n")
    for a in range(-20, 21):
        f.write(f"{a}," + ",".join(f"{return_on_equity(a / 100, L, 0.04) * 100:.2f}" for L in (1, 3, 8)) + "\n")

with open(OUT / "spiral.csv", "w") as f:
    f.write("round,l3,l5,l8\n")
    paths = [spiral(L, 0.05, 0.10) for L in (3, 5, 8)]
    for k in range(12):
        f.write(f"{k + 1}," + ",".join(f"{(p[k] if k < len(p) else p[-1]) * 100:.2f}" for p in paths) + "\n")

with open(OUT / "call_price.csv", "w") as f:
    f.write("initial_pct,call_price_pct\n")
    for m in range(30, 101, 5):
        f.write(f"{m},{margin_call_price(100, m / 100, 0.25):.2f}\n")
