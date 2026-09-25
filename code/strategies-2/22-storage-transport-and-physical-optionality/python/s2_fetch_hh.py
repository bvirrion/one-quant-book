"""Henry Hub summer-winter spreads realised at spot, 2007-2026 (One Quant Book 9, chapter 22).

Downloads from FRED the EIA daily Henry Hub natural gas spot price ($/MMBtu) and, for each storage year from 1997 to
2025 with more than 40 prices in each season (2007 to 2025: FRED's daily series is sparse before 2007), takes the
mean spot price over April to June (injection) and over the following December to February (withdrawal). It writes
only statistics: the number of years, the mean and standard deviation of the winter-minus-summer spread, the number
of years in which it was positive, and the best and worst years; and each year's spread. An unhedged storage
operator who injected evenly in the summer and withdrew evenly in the winter earned this spread, before costs.
Output in data/strategies-2: hh_summary.csv, hh_years.csv. Run once.
"""
from __future__ import annotations

import io
import pathlib
import time
import urllib.request

import pandas as pd

UA = {"User-Agent": "OneQuantBook/1.0 (+https://one-course.com)"}
OUT = pathlib.Path(__file__).resolve().parents[4] / "data" / "strategies-2"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    time.sleep(1)
    raw = urllib.request.urlopen(urllib.request.Request(
        "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DHHNGSP", headers=UA), timeout=60).read()
    df = pd.read_csv(io.BytesIO(raw))
    df.columns = ["date", "v"]
    s = pd.to_numeric(df.set_index(pd.to_datetime(df["date"]))["v"], errors="coerce").dropna()
    rows = []
    for y in range(1997, 2026):
        summer = s[(s.index >= f"{y}-04-01") & (s.index < f"{y}-07-01")]
        winter = s[(s.index >= f"{y}-12-01") & (s.index < f"{y + 1}-03-01")]
        if len(summer) > 40 and len(winter) > 40:
            rows.append((y, round(float(summer.mean()), 3), round(float(winter.mean()), 3),
                         round(float(winter.mean() - summer.mean()), 3)))
    years = pd.DataFrame(rows, columns=["year", "summer", "winter", "spread"])
    years.to_csv(OUT / "hh_years.csv", index=False)
    sp = years["spread"]
    summary = [("first", int(years["year"].iloc[0])), ("last", int(years["year"].iloc[-1])), ("years", len(years)),
               ("mean", float(sp.mean())), ("sd", float(sp.std())), ("positive", int((sp > 0).sum())),
               ("best", float(sp.max())), ("best_year", int(years.loc[sp.idxmax(), "year"])),
               ("worst", float(sp.min())), ("worst_year", int(years.loc[sp.idxmin(), "year"])),
               ("median", float(sp.median()))]
    pd.DataFrame(summary, columns=["key", "value"]).to_csv(OUT / "hh_summary.csv", index=False)


if __name__ == "__main__":
    main()
