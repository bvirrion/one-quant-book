"""Treasury yields around coupon auctions, 2010-2026 (One Quant Book 9, chapter 13).

Downloads from TreasuryDirect's auction query service the note and bond auctions from January 2010 to September 2026
(auction date, term, offering amount, reopening) and from FRED the constant-maturity yields at 2, 5, 7, 10 and 30
years. Auctions are grouped by the nearest benchmark (a 10-year reopening with 9 years 10 months left counts as
10-year). For each auction it measures the benchmark yield's change, in basis points, from five trading days before
to the auction day's close and from the auction day to five days after, and writes only statistics: per benchmark,
the number of auctions and the mean and t-statistic of each change; for the 10-year, the same by third of offering
size; and the average path of the yield (all benchmarks pooled) from ten days before to ten days after, relative to
ten days before. Outputs in data/strategies-2: auctions_summary.csv, auctions_path.csv. Run once.
"""
from __future__ import annotations

import io
import json
import math
import pathlib
import time
import urllib.request

import numpy as np
import pandas as pd

UA = {"User-Agent": "OneQuantBook/1.0 (+https://one-course.com)"}
TD = ("https://www.treasurydirect.gov/TA_WS/securities/search?format=json&securityType={}&dateFieldName=auctionDate"
      "&startDate=01/01/2010&endDate=09/25/2026&pagesize=2000")
BENCH = {"2y": ("DGS2", 2), "5y": ("DGS5", 5), "7y": ("DGS7", 7), "10y": ("DGS10", 10), "30y": ("DGS30", 30)}
OUT = pathlib.Path(__file__).resolve().parents[4] / "data" / "strategies-2"


def _get(url: str) -> bytes:
    time.sleep(1)
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()


def _years(term: str) -> float:
    y = m = 0
    for part in term.split():
        if part.endswith("-Year"):
            y = int(part.split("-")[0])
        if part.endswith("-Month"):
            m = int(part.split("-")[0])
    return y + m / 12


def auctions() -> pd.DataFrame:
    rows = []
    for kind in ("Note", "Bond"):
        for a in json.loads(_get(TD.format(kind))):
            yrs = _years(a["securityTerm"])
            bench = min(BENCH, key=lambda b: abs(BENCH[b][1] - yrs))
            if abs(BENCH[bench][1] - yrs) <= 0.5 and a.get("offeringAmount"):
                rows.append((pd.Timestamp(a["auctionDate"][:10]), bench, float(a["offeringAmount"]) / 1e9))
    return pd.DataFrame(rows, columns=["date", "bench", "size_bn"]).drop_duplicates()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    au = auctions()
    ys = {}
    for b, (sid, _) in BENCH.items():
        df = pd.read_csv(io.BytesIO(_get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}")))
        df.columns = ["date", "y"]
        ys[b] = pd.to_numeric(df.set_index(pd.to_datetime(df["date"]))["y"], errors="coerce").dropna() * 100
    rows, paths = [], []
    for b in BENCH:
        y = ys[b]
        pre, post, size = [], [], []
        for _, a in au[au["bench"] == b].iterrows():
            i = y.index.searchsorted(a["date"])
            if i < 10 or i + 10 >= len(y) or y.index[i] != a["date"]:
                continue
            pre.append(y.iloc[i] - y.iloc[i - 5])
            post.append(y.iloc[i + 5] - y.iloc[i])
            size.append(a["size_bn"])
            paths.append((y.iloc[i - 10:i + 11] - y.iloc[i - 10]).to_numpy())
        pre, post, size = np.array(pre), np.array(post), np.array(size)
        t = lambda x: float(x.mean() / x.std(ddof=1) * math.sqrt(len(x)))            # noqa: E731
        rows += [(b, "n", len(pre)), (b, "pre_mean", float(pre.mean())), (b, "pre_t", t(pre)),
                 (b, "post_mean", float(post.mean())), (b, "post_t", t(post))]
        if b == "10y":
            q = np.quantile(size, [1 / 3, 2 / 3])
            for k, m in enumerate((size <= q[0], (size > q[0]) & (size <= q[1]), size > q[1])):
                rows += [(b, f"size{k + 1}_mean_bn", float(size[m].mean())),
                         (b, f"size{k + 1}_pre", float(pre[m].mean())), (b, f"size{k + 1}_post", float(post[m].mean()))]
    pd.DataFrame(rows, columns=["bench", "stat", "value"]).to_csv(OUT / "auctions_summary.csv", index=False)
    p = np.array(paths)
    pd.DataFrame({"day": np.arange(-10, 11), "mean_bp": p.mean(axis=0), "n": len(p)}).to_csv(
        OUT / "auctions_path.csv", index=False)


if __name__ == "__main__":
    main()
