"""Chart data for Book 3, Chapter 5 (deterministic, from data/markets-3 and the illustrative stack)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_power import day, negative_stats, stack

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "merit.csv", "w") as f:
    f.write("gw,mc\n")
    cum = 0.0
    for _, gw, mc in stack(10):
        f.write(f"{cum:.1f},{mc:.2f}\n")
        cum += gw
    f.write(f"{cum:.1f},{mc:.2f}\n")
with open(OUT / "may11.csv", "w") as f:
    f.write("hour,price,solar,load\n")
    for h, p, s, ld in day(dt.date(2025, 5, 11)):
        f.write(f"{h},{p:.2f},{s:.2f},{ld:.2f}\n")
with open(OUT / "neghours.csv", "w") as f:
    f.write("hour,count\n")
    for h, c in enumerate(negative_stats()["by_hour"]):
        f.write(f"{h},{c}\n")
