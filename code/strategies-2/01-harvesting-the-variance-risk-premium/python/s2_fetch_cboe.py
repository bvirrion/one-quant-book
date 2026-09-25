"""Derived statistics of the S&P 500 variance premium and of Cboe's option-writing indices (One Quant Book 9, ch. 1).

Downloads Cboe's daily histories of the VIX index, the S&P 500 price index (SPX), the Cboe S&P 500 PutWrite index
(PUT) and BuyWrite index (BXM), and writes only statistics computed from them (the raw series are not
redistributed). At each month-end from 1990: VIX squared against the realised variance of SPX log returns over the
next 21 trading days (annualised). For PUT, BXM and SPX from the first month in which PUT is published daily: the
annualised mean return, volatility, Sharpe ratio (no risk-free rate subtracted), maximum drawdown, worst month and
the returns in September-November 2008 and February-March 2020. Outputs in data/strategies-2: vrp_summary.csv,
vrp_worst.csv, vrp_rolling.csv (the 12-month mean of VIX minus realised volatility at each month-end), writers.csv.
Run once; the chapter's tests read the CSVs.
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


def _read(name: str, col: str) -> pd.Series:
    req = urllib.request.Request(BASE + f"{name}_History.csv",
                                 headers={"User-Agent": "OneQuantBook/1.0 (+https://one-course.com)"})
    df = pd.read_csv(io.BytesIO(urllib.request.urlopen(req, timeout=60).read()))
    df["DATE"] = pd.to_datetime(df["DATE"], format="%m/%d/%Y")
    return df.set_index("DATE")[col].astype(float)


def _span(x: pd.Series, a: str, b: str) -> float:
    return float(x[(x.index >= a) & (x.index <= b)].iloc[-1] / x[x.index < a].iloc[-1] - 1)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    vix, spx = _read("VIX", "CLOSE"), _read("SPX", "SPX")
    put, bxm = _read("PUT", "PUT"), _read("BXM", "BXM")
    r = np.log(spx).diff()
    d = pd.concat([vix.rename("vix"), r.rename("r")], axis=1).dropna()
    rv = (d["r"] ** 2).rolling(21).sum().shift(-21) * 252 / 21
    m = pd.DataFrame({"iv": d["vix"] / 100, "rv": np.sqrt(rv)}).dropna()
    me = m.groupby(m.index.to_period("M")).tail(1)
    gap = me["iv"] - me["rv"]
    pd.DataFrame([{"months": len(me), "first": me.index[0].date(), "last": me.index[-1].date(),
                   "mean_vix": me["iv"].mean(), "mean_rv": me["rv"].mean(), "share_above": (gap > 0).mean(),
                   "mean_gap": gap.mean(), "median_gap": gap.median(),
                   "mean_var_ratio": (me["iv"] ** 2).mean() / (me["rv"] ** 2).mean()}]).to_csv(OUT / "vrp_summary.csv",
                                                                                                    index=False)
    worst = (-gap).sort_values(ascending=False).head(6)
    pd.DataFrame({"month_end": [i.date() for i in worst.index], "vix": me.loc[worst.index, "iv"].values,
                  "realised": me.loc[worst.index, "rv"].values}).to_csv(OUT / "vrp_worst.csv", index=False)
    roll = gap.rolling(12).mean().dropna()
    pd.DataFrame({"month_end": [i.date() for i in roll.index], "gap12": roll.values}).to_csv(OUT / "vrp_rolling.csv",
                                                                                            index=False)
    daily_start = put.index[put.index.to_series().diff().dt.days.gt(5)].max()
    idx = pd.concat([put, bxm, spx], axis=1, keys=["PUT", "BXM", "SPX"]).dropna()
    idx = idx[idx.index > daily_start]
    idx = idx[idx.index >= idx.index[idx.index.to_series().dt.month != idx.index[0].month][0]]
    rows = []
    for k in ("PUT", "BXM", "SPX"):
        x = idx[k]
        ret = x.pct_change().dropna()
        mon = x.groupby(x.index.to_period("M")).last().pct_change().dropna()
        dd = (x / x.cummax() - 1).min()
        rows.append({"index": k, "first": idx.index[0].date(), "last": idx.index[-1].date(),
                     "ann_return": float((x.iloc[-1] / x.iloc[0]) ** (252 / len(x)) - 1),
                     "ann_vol": float(ret.std() * math.sqrt(252)),
                     "sharpe": float(ret.mean() / ret.std() * math.sqrt(252)),
                     "max_dd": float(dd), "worst_month": float(mon.min()), "worst_month_at": str(mon.idxmin()),
                     "sep_nov_2008": _span(x, "2008-09-01", "2008-11-30"),
                     "feb_mar_2020": _span(x, "2020-02-01", "2020-03-31")})
    pd.DataFrame(rows).to_csv(OUT / "writers.csv", index=False)


if __name__ == "__main__":
    main()
