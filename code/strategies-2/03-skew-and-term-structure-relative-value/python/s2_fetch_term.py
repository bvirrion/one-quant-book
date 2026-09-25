"""Derived statistics of Cboe's volatility term structure, SKEW index and cross-index vols (One Quant Book 9, ch. 3).

Downloads Cboe's daily histories of VIX, VIX3M (from September 2009), the Cboe SKEW Index (from 1990), and the
Russell 2000 (RVX) and Nasdaq-100 (VXN) volatility indices, and writes only statistics computed from them: for the
slope VIX3M minus VIX, its mean, share of days below zero (VIX above VIX3M), minimum with date, March 2020 monthly mean,
correlation with VIX, and daily AR(1) persistence with its half-life; for SKEW, mean, percentiles, maximum
and minimum with dates, and the correlation of its daily changes with VIX's; for RVX minus VIX and VXN minus VIX,
mean, standard deviation and half-life; and the monthly means of the slope and of VIX (derived series for the
chapter's figure). Outputs in data/strategies-2: term_summary.csv, term_monthly.csv. Run once; the tests read the CSVs.
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


def _ar1(x: pd.Series) -> tuple[float, float]:
    y = x.to_numpy()
    phi = float(np.corrcoef(y[1:], y[:-1])[0, 1])
    return phi, math.log(0.5) / math.log(phi)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    vix, v3m, skew, rvx, vxn = (_read(n) for n in ("VIX", "VIX3M", "SKEW", "RVX", "VXN"))
    slope = (v3m - vix).dropna()
    phi, hl = _ar1(slope)
    mar20 = slope[slope.index.to_period("M") == pd.Period("2020-03")]
    rows = [("slope", "first", str(slope.index[0].date())), ("slope", "last", str(slope.index[-1].date())),
            ("slope", "mean", slope.mean()), ("slope", "share_below_zero", float((slope < 0).mean())),
            ("slope", "min", slope.min()), ("slope", "min_at", str(slope.idxmin().date())),
            ("slope", "mar_2020", mar20.mean()), ("slope", "phi", phi), ("slope", "half_life", hl),
            ("slope", "corr_with_vix", float(np.corrcoef(slope, vix.reindex(slope.index))[0, 1]))]
    q = skew.quantile([0.05, 0.5, 0.95])
    dv = pd.concat([skew.diff(), vix.diff()], axis=1).dropna()
    lv = pd.concat([skew, vix], axis=1).dropna().to_numpy()
    rows += [("skew", "first", str(skew.index[0].date())), ("skew", "mean", skew.mean()),
             ("skew", "p05", q[0.05]), ("skew", "p50", q[0.5]), ("skew", "p95", q[0.95]),
             ("skew", "max", skew.max()), ("skew", "max_at", str(skew.idxmax().date())),
             ("skew", "min", skew.min()), ("skew", "min_at", str(skew.idxmin().date())),
             ("skew", "corr_changes_vix", float(np.corrcoef(dv.iloc[:, 0], dv.iloc[:, 1])[0, 1])),
             ("skew", "corr_levels_vix", float(np.corrcoef(lv[:, 0], lv[:, 1])[0, 1]))]
    for name, other in (("rvx", rvx), ("vxn", vxn)):
        sp = (other - vix).dropna()
        p, h = _ar1(sp)
        rows += [(name, "first", str(sp.index[0].date())), (name, "mean", sp.mean()), (name, "sd", sp.std()),
                 (name, "phi", p), (name, "half_life", h)]
    pd.DataFrame(rows, columns=["series", "stat", "value"]).to_csv(OUT / "term_summary.csv", index=False)
    per = slope.index.to_period("M")
    m = pd.DataFrame({"slope": slope.groupby(per).mean(), "vix": vix.reindex(slope.index).groupby(per).mean()})
    pd.DataFrame({"month": [str(p) for p in m.index], "slope": m["slope"].values, "vix": m["vix"].values}).to_csv(
        OUT / "term_monthly.csv", index=False)


if __name__ == "__main__":
    main()
