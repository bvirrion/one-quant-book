"""Derived statistics of the momentum factor, raw and volatility-scaled (One Quant Book 8, chapter 5).

Downloads the Kenneth R. French Data Library's momentum factor (Mom, monthly and daily) and writes only statistics
computed from it (the library carries a copyright notice and no licence). The volatility-scaled version holds each
month a weight of 12% divided by the annualised volatility of the daily factor over the previous 126 trading days
(the chapter's choice, in the spirit of Barroso and Santa-Clara). Outputs in data/strategies-1: mom_summary.csv (per
version: annualised mean, volatility, Sharpe ratio, skewness, excess kurtosis, worst month and its date, maximum
drawdown with its peak and trough months, the March-May 2009 return and the 2009 calendar-year return), mom_annual.csv
(calendar-year returns of both versions) and mom_worst.csv (the ten worst months of the raw factor, with the scaled
version's return and weight in those months). Run once; the chapter's tests read the CSVs.
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
TARGET, WINDOW = 0.12, 126


def _read(name: str, width: int) -> pd.Series:
    req = urllib.request.Request(BASE + name, headers={"User-Agent": "OneQuantBook/1.0 (+https://one-course.com)"})
    with zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req, timeout=60).read())) as z:
        text = z.read(z.namelist()[0]).decode("latin-1").splitlines()
    head = next(i for i, line in enumerate(text) if line.startswith(","))
    rows = []
    for line in text[head + 1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts[0]) != width or not parts[0].isdigit():
            break
        rows.append((parts[0], float(parts[1]) / 100.0))
    return pd.Series(dict(rows))


def drawdown(r: pd.Series):
    w = (1 + r).cumprod()
    dd = w / w.cummax() - 1
    trough = dd.idxmin()
    peak = w[:trough].idxmax()
    return float(dd.min()), str(peak), str(trough)


def stats(r: pd.Series, label: str) -> dict:
    m, s = r.mean(), r.std(ddof=1)
    z = (r - m) / s
    dd, peak, trough = drawdown(r)
    y09 = r[[k for k in r.index if k.startswith("2009")]]
    return {"version": label, "start": r.index[0], "end": r.index[-1], "months": len(r), "ann_mean": round(12 * m, 6),
            "ann_vol": round(math.sqrt(12) * s, 6), "sharpe": round(math.sqrt(12) * m / s, 4),
            "skew": round(float((z**3).mean()), 4), "exkurt": round(float((z**4).mean() - 3), 4),
            "worst": round(float(r.min()), 6), "worst_month": r.idxmin(), "maxdd": round(dd, 6), "dd_peak": peak,
            "dd_trough": trough, "mar_may_2009": round(float((1 + r[["200903", "200904", "200905"]]).prod() - 1), 6),
            "year_2009": round(float((1 + y09).prod() - 1), 6)}


def main() -> None:
    m = _read("F-F_Momentum_Factor_CSV.zip", 6)
    d = _read("F-F_Momentum_Factor_daily_CSV.zip", 8)
    vol = d.rolling(WINDOW).std(ddof=1) * math.sqrt(252)
    last = vol.groupby(vol.index.str[:6]).last()                 # the volatility known at each month's end
    weight = (TARGET / last).shift(1)                              # held over the next month
    weight = weight.reindex(m.index).dropna()
    raw = m[weight.index]
    scaled = raw * weight
    pd.DataFrame([stats(raw, "raw"), stats(scaled, "scaled")]).to_csv(OUT / "mom_summary.csv", index=False)
    years = sorted({k[:4] for k in raw.index})
    ann = [{"year": int(y), "raw": round(float((1 + raw[raw.index.str[:4] == y]).prod() - 1), 6),
            "scaled": round(float((1 + scaled[scaled.index.str[:4] == y]).prod() - 1), 6)} for y in years]
    pd.DataFrame(ann).to_csv(OUT / "mom_annual.csv", index=False)
    worst = raw.nsmallest(10)
    pd.DataFrame({"month": worst.index, "raw": worst.round(6).values, "scaled": scaled[worst.index].round(6).values,
                  "weight": weight[worst.index].round(4).values}).to_csv(OUT / "mom_worst.csv", index=False)
    print(pd.read_csv(OUT / "mom_summary.csv").T)
    print(pd.read_csv(OUT / "mom_worst.csv"))


if __name__ == "__main__":
    main()
