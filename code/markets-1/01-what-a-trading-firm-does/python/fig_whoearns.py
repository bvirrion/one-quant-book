"""Chart data for Chapter 1 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from whoearns import Day, break_even_volume, simulate_day

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/01-what-a-trading-firm-does"
OUT.mkdir(parents=True, exist_ok=True)

# 1. who earned what on one day (seed 1), in thousands of dollars
d = simulate_day(1)
rows = [("Spread earned", d["mm_spread_earned"]), ("Position P\\&L", d["mm_position_pnl"]),
        ("Rebates", d["mm_rebates"]), ("Market maker net", d["mm_net"]),
        ("Exchange", d["exchange_net"]), ("Broker", d["broker_commission"]),
        ("Clearing house", d["clearing_house"])]
with open(OUT / "whoearns.csv", "w") as f:
    f.write("k,label,usd_thousands\n")
    f.writelines(f"{i},{lab},{v / 1000:.2f}\n" for i, (lab, v) in enumerate(rows))

# 2. distribution of the market maker's daily net over 1000 seeds
nets = np.array([simulate_day(s)["mm_net"] for s in range(1000)]) / 1000
hist, edges = np.histogram(nets, bins=np.arange(-60, 81, 5))
with open(OUT / "daily_net_hist.csv", "w") as f:
    f.write("centre,count\n")
    f.writelines(f"{lo + 2.5:.1f},{c}\n" for lo, c in zip(edges[:-1], hist, strict=True))
with open(OUT / "daily_net_stats.csv", "w") as f:
    f.write("mean,std,share_positive\n")
    f.write(f"{nets.mean():.2f},{nets.std(ddof=1):.2f},{(nets > 0).mean():.3f}\n")

# 3. annual profit against daily volume for a fixed cost base
cap, fixed = 0.0045, 90_000.0
with open(OUT / "break_even.csv", "w") as f:
    f.write("volume_m,profit_m\n")
    f.writelines(f"{v},{(cap * v * 1e6 - fixed) * 252 / 1e6:.3f}\n" for v in range(0, 61, 5))
assert abs(break_even_volume(fixed, cap) - 20e6) < 1e-6
_ = Day
