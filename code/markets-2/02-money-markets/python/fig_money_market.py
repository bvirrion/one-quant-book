"""Chart data for Book 2, Chapter 2 (deterministic)."""
import csv
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from money_market_demo import bill_curve, one_week_by_start

REPO = pathlib.Path(__file__).resolve().parents[4]
OUT = REPO / "figdata/markets-2/02-money-markets"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "bills.csv", "w") as f:
    f.write("weeks,discount,mmy,bey\n")
    for r in bill_curve():
        f.write(f"{r['weeks']},{100 * r['discount']:.4f},{100 * r['mmy']:.4f},{100 * r['bey']:.4f}\n")

START = dt.date(2022, 7, 1)
with open(REPO / "data/markets-2/rrp_ontsyd_2022h2.csv") as src, open(OUT / "rrp.csv", "w") as f:
    f.write("t,usdbn\n")
    for row in csv.DictReader(src):
        if row["RRPONTSYD"]:
            t = (dt.date.fromisoformat(row["observation_date"]) - START).days
            f.write(f"{t},{float(row['RRPONTSYD']):.1f}\n")

with open(OUT / "oneweek.csv", "w") as f:
    f.write("t,rate\n")
    for d, r in one_week_by_start():
        f.write(f"{(d - dt.date(2026, 9, 1)).days + 1},{100 * r:.4f}\n")
