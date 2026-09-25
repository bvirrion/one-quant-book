"""Derived statistics of the factor returns around 6-10 August 2007 (One Quant Book 7, chapter 28).

Downloads the Kenneth R. French Data Library's daily Fama/French 3 factors and daily momentum factor and writes only
statistics computed from them (the library carries a copyright notice and no licence): for Mkt-RF, SMB, HML and Mom,
the standard deviation of daily returns over the 250 trading days to 3 August 2007, the cumulative return from 6 to
9 August 2007 and on 10 August, each also in units of that standard deviation (data/research/ff_aug2007.csv). Run
once; the chapter's tests read the CSV.
"""
from __future__ import annotations

import io
import pathlib
import urllib.request
import zipfile

import pandas as pd

BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
OUT = pathlib.Path(__file__).resolve().parents[4] / "data" / "research"


def daily(name: str) -> pd.DataFrame:
    req = urllib.request.Request(BASE + name, headers={"User-Agent": "OneQuantBook/1.0 (+https://one-course.com)"})
    with zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req, timeout=60).read())) as z:
        text = z.read(z.namelist()[0]).decode("latin-1").splitlines()
    head = next(i for i, line in enumerate(text) if line.startswith(","))
    rows = []
    for line in text[head + 1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts[0]) != 8 or not parts[0].isdigit():
            break
        rows.append(parts)
    cols = ["date"] + [c.strip() for c in text[head].split(",")[1:]]
    df = pd.DataFrame(rows, columns=cols).set_index("date").astype(float) / 100.0
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    return df


def main() -> None:
    df = daily("F-F_Research_Data_Factors_daily_CSV.zip").join(daily("F-F_Momentum_Factor_daily_CSV.zip"), how="inner")
    pre = df[df.index <= "2007-08-03"].tail(250)
    wk = df[(df.index >= "2007-08-06") & (df.index <= "2007-08-09")]
    fri = df[df.index == "2007-08-10"]
    rows = []
    for f in ("Mkt-RF", "SMB", "HML", "Mom"):
        sd = pre[f].std(ddof=1)
        c4, c1 = (1 + wk[f]).prod() - 1, float(fri[f].iloc[0])
        rows.append({"factor": f, "sd_daily": round(sd, 6), "days": len(wk), "cum_6_9": round(c4, 6),
                     "cum_6_9_sd": round(c4 / sd, 3), "aug10": round(c1, 6), "aug10_sd": round(c1 / sd, 3)})
    pd.DataFrame(rows).to_csv(OUT / "ff_aug2007.csv", index=False)
    print(pd.DataFrame(rows))


if __name__ == "__main__":
    main()
