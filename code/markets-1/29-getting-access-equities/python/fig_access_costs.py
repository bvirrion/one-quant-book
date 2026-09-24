"""Chart data for Chapter 29 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from access_costs import MAKER_TAKER, TCV, cost_table, monthly_rebate

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/29-getting-access-equities"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "tiers.csv", "w") as f:
    f.write("adav_m,rebate_mils,monthly_k\n")
    for k in range(1, 401):
        adav = k * 0.1e6
        f.write(f"{adav / 1e6:.1f},{-MAKER_TAKER.add_rate(adav, TCV) * 1e4:.1f},{monthly_rebate(adav) / 1e3:.1f}\n")

with open(OUT / "venues.csv", "w") as f:
    f.write("venue,passive_mils,aggressive_mils\n")
    for name, p, a in cost_table(9e6):
        f.write(f"{name.split()[0]},{p * 1e4:.1f},{a * 1e4:.1f}\n")
