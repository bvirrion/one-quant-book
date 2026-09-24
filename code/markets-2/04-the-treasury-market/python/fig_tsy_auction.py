"""Chart data for Book 2, Chapter 4 (deterministic)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from tsy_auction_demo import demand_curve, fed_treasuries

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-2/04-the-treasury-market"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "demand.csv", "w") as f:
    f.write("yield,cumbn\n")
    for y, c in demand_curve():
        f.write(f"{100 * y:.3f},{c / 1000:.3f}\n")

START = dt.date(2019, 12, 4)
with open(OUT / "fed2020.csv", "w") as f:
    f.write("t,usdbn\n")
    for d, v in fed_treasuries():
        f.write(f"{(d - START).days},{v:.1f}\n")
