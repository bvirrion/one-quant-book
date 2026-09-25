"""Chart data for Book 9, chapter 23 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_powergas import battery_table, hourly  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

d = hourly()
by = d.groupby(["year", "hour"])["price"].mean()
neg = (d["price"] < 0).groupby(d["hour"]).mean() * 100
with open(OUT / "profile.csv", "w") as f:
    f.write("hour,p2024,p2025,negative\n")
    for h in range(24):
        f.write(f"{h},{by[(2024, h)]:.2f},{by[(2025, h)]:.2f},{neg[h]:.2f}\n")

b = battery_table()
with open(OUT / "battery.csv", "w") as f:
    f.write("day,da,total\n")
    for i in range(0, len(b["cum_da"]), 3):
        f.write(f"{i + 1},{b['cum_da'][i] / 1000:.3f},{b['cum_total'][i] / 1000:.3f}\n")
    if (len(b["cum_da"]) - 1) % 3:
        f.write(f"{len(b['cum_da'])},{b['cum_da'][-1] / 1000:.3f},{b['cum_total'][-1] / 1000:.3f}\n")
