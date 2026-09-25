"""Derived statistics of Cboe's put-protection and collar indices (One Quant Book 9, chapter 7).

Downloads Cboe's daily histories of the S&P 500 5% Put Protection Index (PPUT, total return, from June 1986), the
S&P 500 95-110 Collar Index (CLL, from 2008 in this file) and the zero-cost put-spread collar index (CLLZ, from June
1986), and the S&P 500 price index (SPX, which omits dividends), and writes only statistics over the common period
from 30 June 1986 to 22 September 2026: annualised log return, volatility, maximum drawdown with its peak and trough
dates, worst 21-day return, and the returns over October 1987 (30 September to 30 October), September to November
2008 and February to March 2020; and the yearly returns of PPUT, CLLZ and SPX. Outputs in data/strategies-2:
protect_summary.csv, protect_yearly.csv. Run once; the tests read the CSVs.
"""
from __future__ import annotations

import io
import math
import pathlib
import urllib.request

import numpy as np
import pandas as pd

BASE = "https://cdn.cboe.com/api/global/us_indices/daily_prices/"
OUT = pathlib.Path(__file__).resolve().parents[4] / "data" / "strategies-2"


def _read(name: str) -> pd.Series:
    req = urllib.request.Request(BASE + f"{name}_History.csv",
                                 headers={"User-Agent": "OneQuantBook/1.0 (+https://one-course.com)"})
    df = pd.read_csv(io.BytesIO(urllib.request.urlopen(req, timeout=60).read()))
    df["DATE"] = pd.to_datetime(df["DATE"], format="%m/%d/%Y")
    col = "CLOSE" if "CLOSE" in df.columns else name
    x = df.set_index("DATE")[col].astype(float)
    return x[x > 0]


def _span(x: pd.Series, a: str, b: str) -> float:
    s = x[a:b]
    return float(s.iloc[-1] / s.iloc[0] - 1)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    px = pd.concat({n: _read(n) for n in ("PPUT", "CLLZ", "SPX")}, axis=1).dropna()
    px = px[px.index >= "1986-06-30"]
    rows = []
    for n in px.columns:
        x = px[n]
        lr = np.log(x).diff().dropna()
        years = (x.index[-1] - x.index[0]).days / 365.25
        rows.append({"index": n, "first": str(x.index[0].date()), "last": str(x.index[-1].date()),
                     "ann_log": math.log(x.iloc[-1] / x.iloc[0]) / years, "vol": float(lr.std() * math.sqrt(252)),
                     "max_dd": float((x / x.cummax() - 1).min()), "worst_21d": float((x / x.shift(21) - 1).min()),
                     "dd_trough": str((x / x.cummax() - 1).idxmin().date()),
                     "dd_peak": str(x[:(x / x.cummax() - 1).idxmin()].idxmax().date()),
                     "oct_1987": _span(x, "1987-09-30", "1987-10-30"),
                     "autumn_2008": _span(x, "2008-08-29", "2008-11-28"),
                     "covid_2020": _span(x, "2020-01-31", "2020-03-31")})
    pd.DataFrame(rows).to_csv(OUT / "protect_summary.csv", index=False)
    y = px.groupby(px.index.year).agg(["first", "last"])
    yearly = pd.DataFrame({n: y[(n, "last")] / y[(n, "first")] - 1 for n in px.columns})
    yearly.index.name = "year"
    yearly.to_csv(OUT / "protect_yearly.csv")


if __name__ == "__main__":
    main()
