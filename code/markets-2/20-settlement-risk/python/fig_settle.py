"""Chart data for Book 2, Chapter 20 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from settle_demo import profiles

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
p = profiles()
with open(OUT / "exposure.csv", "w") as f:
    f.write("t,gross,net,pvp\n")
    for (t, g), (_, n), (_, v) in zip(p["gross"], p["net"], p["pvp"], strict=True):
        f.write(f"{t:.2f},{g / 1e6:.1f},{n / 1e6:.1f},{v / 1e6:.1f}\n")
