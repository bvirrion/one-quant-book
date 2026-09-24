"""Chart data for Chapter 4 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from venue_econ import ACCESS, ICE_EXCHANGES_2025, monthly_cost, venue_profit

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/04-exchanges-brokers-venues"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "ice_exchanges_2025.csv", "w") as f:
    f.write("k,label,usd_m\n")
    f.writelines(f"{i},{k},{v}\n" for i, (k, v) in enumerate(ICE_EXCHANGES_2025.items()))

with open(OUT / "access_cost.csv", "w") as f:
    f.write("shares_m," + ",".join(m.name.replace(" ", "_") for m in ACCESS) + "\n")
    v = 0.1
    while v <= 2000:
        cents = [monthly_cost(m, v * 1e6) / (v * 1e6) * 100 for m in ACCESS]
        f.write(f"{v:.3f}," + ",".join(f"{c:.4f}" for c in cents) + "\n")
        v *= 1.12

with open(OUT / "venue_profit.csv", "w") as f:
    f.write("share_pct,profit_m\n")
    f.writelines(f"{s},{venue_profit(s / 100, 10e9, 0.0003, 50e6, 40e6) / 1e6:.2f}\n" for s in range(0, 21))
