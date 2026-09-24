"""Chart data for Book 3, Chapter 19 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_etf import delta_table, expiry_value_coin

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "expiry.csv", "w") as f:
    f.write("price,call_coin,put_coin\n")
    for p in range(30_000, 180_001, 5_000):
        f.write(f"{p},{expiry_value_coin(p, 90_000, 'C'):.5f},{expiry_value_coin(p, 90_000, 'P'):.5f}\n")

with open(OUT / "deltas.csv", "w") as f:
    f.write("strike,forward,adjusted\n")
    for k, _, _, d, pa in delta_table():
        f.write(f"{k / 1000:.0f},{d:.4f},{pa:.4f}\n")
