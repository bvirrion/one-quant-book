"""Derived statistics of Cboe's 1-month implied correlation index and dispersion index (One Quant Book 9, ch. 2).

Downloads Cboe's daily histories of the Cboe 1-Month Implied Correlation Index (COR1M, from January 2006) and the Cboe
S&P 500 Dispersion Index (DSPX, from June 2014) and writes only statistics computed from them: for each, the first and
last dates, mean, standard deviation, 5th, 50th and 95th percentiles, maximum and minimum with their dates, the
monthly average in October 2008 and March 2020 where available, and the last value; and the monthly average of COR1M
(a derived series for the chapter's figure). Outputs in data/strategies-2: cor_summary.csv, cor_monthly.csv.
Run once; the chapter's tests read the CSVs.
"""
from __future__ import annotations

import io
import pathlib
import urllib.request

import pandas as pd

BASE = "https://cdn.cboe.com/api/global/us_indices/daily_prices/"
OUT = pathlib.Path(__file__).resolve().parents[4] / "data" / "strategies-2"


def _read(name: str) -> pd.Series:
    req = urllib.request.Request(BASE + f"{name}_History.csv",
                                 headers={"User-Agent": "OneQuantBook/1.0 (+https://one-course.com)"})
    df = pd.read_csv(io.BytesIO(urllib.request.urlopen(req, timeout=60).read()))
    df["DATE"] = pd.to_datetime(df["DATE"], format="%m/%d/%Y")
    col = "CLOSE" if "CLOSE" in df.columns else name
    return df.set_index("DATE")[col].astype(float)


def _month(x: pd.Series, ym: str) -> float:
    m = x[x.index.to_period("M") == pd.Period(ym)]
    return float(m.mean()) if len(m) else float("nan")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    series = {k: v[v > 0] for k, v in (("COR1M", _read("COR1M")), ("DSPX", _read("DSPX")))}   # zeros are gaps
    for name, x in series.items():
        q = x.quantile([0.05, 0.5, 0.95])
        rows.append({"index": name, "first": x.index[0].date(), "last": x.index[-1].date(), "mean": x.mean(),
                     "sd": x.std(), "p05": q[0.05], "p50": q[0.5], "p95": q[0.95], "max": x.max(),
                     "max_at": x.idxmax().date(), "min": x.min(), "min_at": x.idxmin().date(),
                     "oct_2008": _month(x, "2008-10"), "mar_2020": _month(x, "2020-03"), "last_value": x.iloc[-1]})
    pd.DataFrame(rows).to_csv(OUT / "cor_summary.csv", index=False)
    m = series["COR1M"].groupby(series["COR1M"].index.to_period("M")).mean()
    pd.DataFrame({"month": [str(p) for p in m.index], "cor1m": m.values}).to_csv(OUT / "cor_monthly.csv", index=False)


if __name__ == "__main__":
    main()
