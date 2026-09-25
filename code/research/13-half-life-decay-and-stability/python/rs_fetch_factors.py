"""Derived decay statistics of the size, value and momentum factors (One Quant Book 7, chapter 13).

Downloads the Kenneth R. French Data Library's monthly Fama/French 3 factors and momentum factor and writes only
statistics computed from them (the library carries a copyright notice and no licence): for SMB, HML and Mom, the mean
monthly return, its standard deviation and t statistic from July 1963 to the end of the year the factor's paper was
published and from the next month to the end of the data, the sup-F statistic of one break in the mean over the whole
monthly history from July 1963 with its permutation p-value and date, and the 120-month rolling mean at each
December (data/research/ff_decay.csv and ff_decay_rolling.csv). Run once; the chapter's tests read the CSVs.
"""
from __future__ import annotations

import io
import pathlib
import sys
import urllib.request
import zipfile

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "decay"))
from firm_decay import sup_f, sup_f_pvalue  # noqa: E402

BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
OUT = pathlib.Path(__file__).resolve().parents[4] / "data" / "research"
# Banz (1981), Fama and French (1992), Jegadeesh and Titman (1993)
PAPERS = {"SMB": 1981, "HML": 1992, "Mom": 1993}
START = "1963-07"


def monthly(name: str) -> pd.DataFrame:
    req = urllib.request.Request(BASE + name, headers={"User-Agent": "Mozilla/5.0"})
    with zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req, timeout=60).read())) as z:
        text = z.read(z.namelist()[0]).decode("latin-1").splitlines()
    head = next(i for i, line in enumerate(text) if line.startswith(","))           # the column header row
    rows = []
    for line in text[head + 1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts[0]) != 6 or not parts[0].isdigit():
            break
        rows.append(parts)
    cols = ["date"] + [c.strip() for c in text[head].split(",")[1:]]
    df = pd.DataFrame(rows, columns=cols).set_index("date").astype(float) / 100.0
    df.index = pd.PeriodIndex([f"{d[:4]}-{d[4:]}" for d in df.index], freq="M")
    return df


def main() -> None:
    df = monthly("F-F_Research_Data_Factors_CSV.zip").join(monthly("F-F_Momentum_Factor_CSV.zip"), how="inner")
    df = df[df.index >= pd.Period(START, "M")]
    rows, roll = [], []
    for f, year in PAPERS.items():
        x = df[f]
        for label, part in (("before", x[x.index.year <= year]), ("after", x[x.index.year > year])):
            rows.append({"factor": f, "published": year, "period": label, "start": str(part.index[0]),
                         "end": str(part.index[-1]), "months": len(part), "mean": round(part.mean(), 6),
                         "sd": round(part.std(ddof=1), 6),
                         "t": round(part.mean() / part.std(ddof=1) * np.sqrt(len(part)), 4)})
        stat, k = sup_f(x.to_numpy())
        rows.append({"factor": f, "published": year, "period": "break", "start": str(x.index[k]), "end": "",
                     "months": len(x), "mean": round(stat, 4), "sd": "",
                     "t": round(sup_f_pvalue(x.to_numpy(), reps=2000, seed=1), 4)})
        r = x.rolling(120).mean()
        for p, v in r[(r.index.month == 12) & r.notna()].items():
            roll.append({"factor": f, "year": p.year, "mean": round(v, 6)})
    pd.DataFrame(rows).to_csv(OUT / "ff_decay.csv", index=False)
    pd.DataFrame(roll).to_csv(OUT / "ff_decay_rolling.csv", index=False)


if __name__ == "__main__":
    main()
