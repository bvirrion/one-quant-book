"""Regenerate data/desk/vix_annual.csv from Cboe's public VIX history (network; not run by the tests).

Cboe's index data carry no redistribution licence: only the annual mean of daily closes is written.
    .venv/bin/python code/desk/01-the-economics-of-a-trading-firm/python/fm_fetch_vix.py
"""
import collections
import csv
import io
import pathlib
import urllib.request

URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
OUT = pathlib.Path(__file__).resolve().parents[4] / "data/desk/vix_annual.csv"


def main(first=2019, last=2025):
    raw = urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})).read().decode()
    by_year = collections.defaultdict(list)
    for r in csv.DictReader(io.StringIO(raw)):
        by_year[int(r["DATE"][-4:])].append(float(r["CLOSE"]))
    with open(OUT, "w") as f:
        f.write("year,vix_mean,days\n")
        for y in range(first, last + 1):
            v = by_year[y]
            f.write(f"{y},{sum(v) / len(v):.2f},{len(v)}\n")


if __name__ == "__main__":
    main()
