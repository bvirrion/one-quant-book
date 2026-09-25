"""Derived statistics of value, profitability, investment and beta-sorted portfolios (One Quant Book 8, chapter 6).

Downloads the Kenneth R. French Data Library's monthly Fama/French five factors (2x3) and the value-weighted
portfolios formed on beta, and writes only statistics computed from them (the library carries a copyright notice and
no licence), into data/strategies-1: ff5_summary.csv (annualised mean, volatility, Sharpe ratio and t statistic of
Mkt-RF, SMB, HML, RMW and CMA over July 1963 to July 2026 and over three periods), ff5_corr.csv (correlations of the
factors and the momentum factor over the whole sample and over 2007-2020), hml_drawdown.csv (the value factor's
drawdown that began in 2007: peak, trough, depth, and whether it had been recovered by the end of the data),
ff5_rolling.csv (120-month rolling annualised means of HML and RMW at each December) and beta_sml.csv (for the ten
beta deciles: annualised mean excess return and realised beta on Mkt-RF, and a betting-against-beta portfolio built
from the extreme quintiles with 60-month rolling betas known before each month). Run once; the chapter's tests read
the CSVs.
"""
from __future__ import annotations

import io
import math
import pathlib
import urllib.request
import zipfile

import numpy as np
import pandas as pd

BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
OUT = pathlib.Path(__file__).resolve().parents[4] / "data" / "strategies-1"


def _lines(name: str):
    req = urllib.request.Request(BASE + name, headers={"User-Agent": "OneQuantBook/1.0 (+https://one-course.com)"})
    with zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req, timeout=60).read())) as z:
        return z.read(z.namelist()[0]).decode("latin-1").splitlines()


def _table(text, head: int) -> pd.DataFrame:
    cols = [c.strip() for c in text[head].split(",")[1:]]
    rows = []
    for line in text[head + 1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts[0]) != 6 or not parts[0].isdigit():
            break
        rows.append([parts[0]] + [float(p) / 100.0 for p in parts[1:]])
    return pd.DataFrame(rows, columns=["month"] + cols).set_index("month")


def stats(x: pd.Series, label: str, period: str) -> dict:
    m, s = x.mean(), x.std(ddof=1)
    return {"factor": label, "period": period, "start": x.index[0], "end": x.index[-1], "ann_mean": round(12 * m, 6),
            "ann_vol": round(math.sqrt(12) * s, 6), "sharpe": round(math.sqrt(12) * m / s, 4),
            "t": round(m / s * math.sqrt(len(x)), 4)}


def main() -> None:
    t5 = _lines("F-F_Research_Data_5_Factors_2x3_CSV.zip")
    f = _table(t5, next(i for i, line in enumerate(t5) if line.startswith(",")))
    periods = {"1963-2026": (None, None), "1963-2006": (None, "200612"), "2007-2020": ("200701", "202012"),
               "2021-2026": ("202101", None)}
    rows = []
    for k in ("Mkt-RF", "SMB", "HML", "RMW", "CMA"):
        for p, (a, b) in periods.items():
            x = f[k]
            if a:
                x = x[x.index >= a]
            if b:
                x = x[x.index <= b]
            rows.append(stats(x, k, p))
    pd.DataFrame(rows).to_csv(OUT / "ff5_summary.csv", index=False)
    tm = _lines("F-F_Momentum_Factor_CSV.zip")
    mom = _table(tm, next(i for i, line in enumerate(tm) if line.startswith(",")))
    f = f.join(mom, how="inner")
    cols = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "Mom"]
    c1 = f[cols].corr().round(4)
    c2 = f.loc["200701":"202012", cols].corr().round(4)
    pd.concat({"1963-2026": c1, "2007-2020": c2}).rename_axis(["period", "factor"]).to_csv(OUT / "ff5_corr.csv")
    w = (1 + f["HML"]).cumprod()
    dd = w / w.cummax() - 1
    trough = dd.loc["200701":"202112"].idxmin()
    peak = w.loc[:trough].idxmax()
    after = w.loc[trough:]
    rec = after[after >= w[peak]]
    pd.DataFrame([{"peak": peak, "trough": trough, "depth": round(float(dd[trough]), 6),
                   "recovered": rec.index[0] if len(rec) else "", "end_dd": round(float(dd.iloc[-1]), 6),
                   "gain_to_peak": round(float(w[peak] - 1), 6)}]).to_csv(OUT / "hml_drawdown.csv", index=False)
    roll = (12 * f[["HML", "RMW"]].rolling(120).mean())
    dec = roll[[m.endswith("12") for m in roll.index]].dropna()
    pd.DataFrame({"year": [int(m[:4]) for m in dec.index], "hml": dec["HML"].round(6).values,
                  "rmw": dec["RMW"].round(6).values}).to_csv(OUT / "ff5_rolling.csv", index=False)
    tb = _lines("Portfolios_Formed_on_BETA_CSV.zip")
    start = next(i for i, line in enumerate(tb) if "Value Weighted Returns -- Monthly" in line)
    vw = _table(tb, start + 1)
    vw = vw.loc[vw.index.isin(f.index)]
    ex = vw.sub(f.loc[vw.index, "RF"], axis=0)
    mk = f.loc[vw.index, "Mkt-RF"]
    dec = ["Lo 10"] + [f"Dec {i}" for i in range(2, 10)] + ["Hi 10"]
    sml = [{"portfolio": d, "ann_excess": round(12 * ex[d].mean(), 6),
            "beta": round(float(np.cov(ex[d], mk)[0, 1] / mk.var(ddof=1)), 4)} for d in dec]
    bl = ex["Lo 20"].rolling(60).cov(mk) / mk.rolling(60).var()
    bh = ex["Hi 20"].rolling(60).cov(mk) / mk.rolling(60).var()
    bab = (ex["Lo 20"] / bl.shift(1) - ex["Hi 20"] / bh.shift(1)).dropna()
    s = stats(bab, "BAB quintiles", f"{bab.index[0]}-{bab.index[-1]}")
    s["beta"] = round(float(np.cov(bab, mk[bab.index])[0, 1] / mk[bab.index].var(ddof=1)), 4)
    sml.append({"portfolio": "BAB", "ann_excess": s["ann_mean"], "beta": s["beta"], "sharpe": s["sharpe"], "t": s["t"],
                "ann_vol": s["ann_vol"], "start": bab.index[0]})
    pd.DataFrame(sml).to_csv(OUT / "beta_sml.csv", index=False)
    print(pd.read_csv(OUT / "ff5_summary.csv").to_string())
    print(pd.read_csv(OUT / "ff5_corr.csv").to_string())
    print(pd.read_csv(OUT / "hml_drawdown.csv").to_string())
    print(pd.read_csv(OUT / "beta_sml.csv").to_string())


if __name__ == "__main__":
    main()
