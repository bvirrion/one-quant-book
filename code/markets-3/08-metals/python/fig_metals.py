"""Chart data for Book 3, Chapter 8 (deterministic)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_metals import NICKEL

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/prompts"))
from firm_prompts import prompt_dates

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "nickel.csv", "w") as f:
    f.write("i,h,price\n")
    for i, (_, h, p) in enumerate(NICKEL, start=1):
        f.write(f"{i},{h},{p / 1000:.3f}\n")
trade = dt.date(2026, 9, 24)
p = prompt_dates(trade)
with open(OUT / "prompts.csv", "w") as f:
    f.write("months,row\n")
    for row, key in ((3, "daily"), (2, "weekly"), (1, "monthly")):
        for d in p[key]:
            f.write(f"{(d - trade).days / 30.4375:.3f},{row}\n")
