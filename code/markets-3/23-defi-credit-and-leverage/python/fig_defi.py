"""Chart data for Book 3, Chapter 23 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_defi import health_path, pump_attack, rate_curve

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "rates.csv", "w") as f:
    f.write("u,borrow,supply\n")
    for u, rb, rs in rate_curve():
        f.write(f"{100 * u:.0f},{100 * rb:.3f},{100 * rs:.3f}\n")

with open(OUT / "health.csv", "w") as f:
    f.write("price,hf\n")
    for p, h in health_path():
        f.write(f"{p},{h:.4f}\n")

with open(OUT / "pump.csv", "w") as f:
    f.write("k,gain\n")
    for i in range(10, 401, 5):
        k = i / 10
        f.write(f"{k:.1f},{pump_attack(k) / 1e6:.3f}\n")
