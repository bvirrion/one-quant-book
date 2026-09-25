"""Derived statistics of US dollar swap spreads, 2000-2016 (One Quant Book 9, chapter 12).

Downloads from FRED the ICE (formerly ISDA) US dollar swap rates at 2, 5, 10 and 30 years (DSWP2 ... DSWP30,
published there from July 2000 to October 2016) and the Board's constant-maturity Treasury yields at the same
maturities (DGS2 ... DGS30), and writes only statistics of the swap spread (swap rate minus Treasury yield, in basis
points) for each maturity: its mean before October 2008 and from October 2008, the share of days below zero from
October 2008, its minimum with date and its last value; and the monthly mean spreads at 10 and 30 years (a derived
series for the chapter's figure). Outputs in data/strategies-2: swaps_summary.csv, swaps_monthly.csv. Run once.
"""
from __future__ import annotations

import io
import pathlib
import time
import urllib.request

import pandas as pd

OUT = pathlib.Path(__file__).resolve().parents[4] / "data" / "strategies-2"
PAIRS = {"2y": ("DSWP2", "DGS2"), "5y": ("DSWP5", "DGS5"), "10y": ("DSWP10", "DGS10"), "30y": ("DSWP30", "DGS30")}


def _read(sid: str) -> pd.Series:
    time.sleep(1)
    req = urllib.request.Request(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}",
                                 headers={"User-Agent": "OneQuantBook/1.0 (+https://one-course.com)"})
    df = pd.read_csv(io.BytesIO(urllib.request.urlopen(req, timeout=60).read()))
    df.columns = ["date", sid]
    return df.set_index(pd.to_datetime(df["date"]))[sid].pipe(pd.to_numeric, errors="coerce")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, monthly = [], {}
    for name, (sw, ts) in PAIRS.items():
        s = ((_read(sw) - _read(ts)) * 100).dropna()
        pre, post = s[s.index < "2008-10-01"], s[s.index >= "2008-10-01"]
        rows += [(name, "first", str(s.index[0].date())), (name, "last", str(s.index[-1].date())),
                 (name, "mean_pre", float(pre.mean())), (name, "mean_post", float(post.mean())),
                 (name, "neg_share_post", float((post < 0).mean())), (name, "min", float(s.min())),
                 (name, "min_at", str(s.idxmin().date())), (name, "last_value", float(s.iloc[-1]))]
        if name in ("10y", "30y"):
            monthly[name] = s.groupby(s.index.to_period("M")).mean()
    pd.DataFrame(rows, columns=["maturity", "stat", "value"]).to_csv(OUT / "swaps_summary.csv", index=False)
    m = pd.DataFrame(monthly)
    pd.DataFrame({"month": [str(p) for p in m.index], "s10": m["10y"].values, "s30": m["30y"].values}).to_csv(
        OUT / "swaps_monthly.csv", index=False)


if __name__ == "__main__":
    main()
