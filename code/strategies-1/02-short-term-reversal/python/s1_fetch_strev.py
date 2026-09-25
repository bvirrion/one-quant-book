"""Derived statistics of the short-term reversal factor (One Quant Book 8, chapter 2).

Downloads the Kenneth R. French Data Library's monthly short-term reversal factor (ST_Rev: low minus high prior-month
return, value weighted, big and small averaged) and writes only statistics computed from it (the library carries a
copyright notice and no licence): the mean, volatility, Sharpe ratio and t statistic of the monthly factor by decade
and before and after the end of 1989 (the year after Jegadeesh (1990)'s sample and Lehmann (1990) appeared), into
data/strategies-1/strev_periods.csv; its 120-month rolling annualised mean at each December into strev_rolling.csv.
Run once; the chapter's tests read the CSVs.
"""
from __future__ import annotations

import io
import math
import pathlib
import urllib.request
import zipfile

import pandas as pd

BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
OUT = pathlib.Path(__file__).resolve().parents[4] / "data" / "strategies-1"


def monthly(name: str) -> pd.Series:
    req = urllib.request.Request(BASE + name, headers={"User-Agent": "OneQuantBook/1.0 (+https://one-course.com)"})
    with zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req, timeout=60).read())) as z:
        text = z.read(z.namelist()[0]).decode("latin-1").splitlines()
    head = next(i for i, line in enumerate(text) if line.startswith(","))
    rows = []
    for line in text[head + 1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts[0]) != 6 or not parts[0].isdigit():
            break
        rows.append((parts[0], float(parts[1]) / 100.0))
    s = pd.Series(dict(rows))
    s.index = pd.PeriodIndex([f"{k[:4]}-{k[4:]}" for k in s.index], freq="M")
    return s


def stats(x: pd.Series, label: str) -> dict:
    m, sd = x.mean(), x.std(ddof=1)
    return {"period": label, "start": str(x.index[0]), "end": str(x.index[-1]), "months": len(x),
            "ann_mean": round(12 * m, 6), "ann_vol": round(math.sqrt(12) * sd, 6),
            "sharpe": round(math.sqrt(12) * m / sd, 4), "t": round(m / sd * math.sqrt(len(x)), 4)}


def main() -> None:
    s = monthly("F-F_ST_Reversal_Factor_CSV.zip")
    rows = [stats(s, "all")]
    rows += [stats(s[s.index.year <= 1989], "to 1989"), stats(s[s.index.year >= 1990], "from 1990")]
    for d in range(1920, 2030, 10):
        x = s[(s.index.year >= d) & (s.index.year < d + 10)]
        if len(x) >= 24:
            rows.append(stats(x, f"{d}s"))
    pd.DataFrame(rows).to_csv(OUT / "strev_periods.csv", index=False)
    roll = (12 * s.rolling(120).mean())[s.index.month == 12].dropna()
    pd.DataFrame({"year": roll.index.year, "mean": roll.round(6).values}).to_csv(OUT / "strev_rolling.csv", index=False)
    print(pd.DataFrame(rows))


if __name__ == "__main__":
    main()
