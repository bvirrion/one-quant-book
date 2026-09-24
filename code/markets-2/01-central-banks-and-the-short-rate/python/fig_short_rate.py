"""Chart data for Book 2, Chapter 1 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from short_rate_demo import END, fed_balance_sheet, overnight_rate, running_compounded

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-2/01-central-banks-and-the-short-rate"
OUT.mkdir(parents=True, exist_ok=True)

bs = fed_balance_sheet()
a, liab = bs["assets"], bs["liabilities"]
with open(OUT / "balance.csv", "w") as f:
    f.write("side,treasuries,mbs,otherassets,reserves,tga,rrp,currency\n")
    f.write(f"assets,{a['Treasuries']:.1f},{a['MBS']:.1f},{a['other']:.1f},0,0,0,0\n")
    f.write(f"liabilities,0,0,0,{liab['reserves']:.1f},{liab['TGA']:.1f},{liab['reverse repo']:.1f},"
            f"{liab['currency and other']:.1f}\n")

with open(OUT / "corridor.csv", "w") as f:
    f.write("reserves,rate\n")
    for i in range(0, 61):
        r = i / 10
        f.write(f"{r:.1f},{100 * overnight_rate(r, 0.0250, 0.0290):.4f}\n")

with open(OUT / "month.csv", "w") as f:
    f.write("day,fixing,compounded\n")
    rows = running_compounded()
    for d, fix, comp in rows:
        f.write(f"{d.day},{100 * fix:.4f},{100 * comp:.4f}\n")
    # close the step plot at the period end (1 October = day 31 of the chart)
    f.write(f"{(END - rows[0][0]).days + 1},{100 * rows[-1][1]:.4f},{100 * rows[-1][2]:.4f}\n")
