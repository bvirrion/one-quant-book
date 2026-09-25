"""Derived statistics of US Treasury constant-maturity yields (One Quant Book 9, chapter 10).

Downloads from FRED the Board of Governors' H.15 constant-maturity Treasury yields at 1, 2, 3, 5, 7, 10 and 20
years (DGS1 ... DGS20) and keeps the days on which all seven are published, from 3 January 1994 to the last common
day. It writes only statistics: the share of the variance of daily yield changes explained by each of the first three
principal components and their loadings; and for the 2-5-10 butterfly (2 x 5-year minus 2-year minus 10-year, in
basis points), its mean, standard deviation, daily AR(1) persistence and half-life, and the monthly mean (a derived
series for the chapter's figure). Outputs in data/strategies-2: ust_summary.csv, ust_fly_monthly.csv. Run once.
"""
from __future__ import annotations

import io
import math
import pathlib
import time
import urllib.request

import numpy as np
import pandas as pd

IDS = ("DGS1", "DGS2", "DGS3", "DGS5", "DGS7", "DGS10", "DGS20")
OUT = pathlib.Path(__file__).resolve().parents[4] / "data" / "strategies-2"


def _read(sid: str) -> pd.Series:
    time.sleep(1)
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
    req = urllib.request.Request(url, headers={"User-Agent": "OneQuantBook/1.0 (+https://one-course.com)"})
    df = pd.read_csv(io.BytesIO(urllib.request.urlopen(req, timeout=60).read()))
    df.columns = ["date", sid]
    df[sid] = pd.to_numeric(df[sid], errors="coerce")
    return df.set_index(pd.to_datetime(df["date"]))[sid]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    y = pd.concat([_read(s) for s in IDS], axis=1).dropna()
    y = y[y.index >= "1994-01-01"]
    dy = y.diff().dropna() * 100                                     # basis points
    vals, vecs = np.linalg.eigh(np.cov(dy.to_numpy().T))
    order = np.argsort(vals)[::-1]
    share = vals[order] / vals.sum()
    rows = [("first", str(y.index[0].date())), ("last", str(y.index[-1].date())), ("days", len(y))]
    for k in range(3):
        v = vecs[:, order[k]] * np.sign(vecs[:, order[k]].sum() if k == 0 else vecs[-1, order[k]])
        rows.append((f"pc{k + 1}_share", float(share[k])))
        rows += [(f"pc{k + 1}_{s}", float(x)) for s, x in zip(IDS, v, strict=True)]
    fly = (2 * y["DGS5"] - y["DGS2"] - y["DGS10"]) * 100
    phi = float(np.corrcoef(fly.to_numpy()[1:], fly.to_numpy()[:-1])[0, 1])
    rows += [("fly_mean", float(fly.mean())), ("fly_sd", float(fly.std())), ("fly_phi", phi),
             ("fly_half_life", math.log(0.5) / math.log(phi)), ("fly_min", float(fly.min())),
             ("fly_max", float(fly.max()))]
    pd.DataFrame(rows, columns=["stat", "value"]).to_csv(OUT / "ust_summary.csv", index=False)
    m = fly.groupby(fly.index.to_period("M")).mean()
    pd.DataFrame({"month": [str(p) for p in m.index], "fly": m.values}).to_csv(OUT / "ust_fly_monthly.csv", index=False)


if __name__ == "__main__":
    main()
