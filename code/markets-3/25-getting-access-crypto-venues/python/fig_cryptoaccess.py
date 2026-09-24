"""Chart data for Book 3, Chapter 25 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_cryptoaccess import effective_fee_curve, quoting_snapshots, spread_vs_concentrate, uptime

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

spread, conc = spread_vs_concentrate()
with open(OUT / "fees.csv", "w") as f:
    f.write("venue,spread,concentrated\n")
    for v in spread:
        f.write(f"{v},{spread[v] / 1000:.2f},{conc.get(v, 0.0) / 1000:.2f}\n")

a, b = quoting_snapshots(thin_at=2.0), quoting_snapshots(thin_at=2.25)
with open(OUT / "uptime.csv", "w") as f:
    f.write("max_spread,thin20,thin225\n")
    for s in range(4, 41, 2):
        f.write(f"{s},{100 * uptime(a, s, 50_000):.2f},{100 * uptime(b, s, 50_000):.2f}\n")

with open(OUT / "feecurve.csv", "w") as f:
    f.write("vol_m,binance_bp,kraken_bp\n")
    for v, b, k in effective_fee_curve():
        f.write(f"{v:.4f},{b:.3f},{k:.3f}\n")
