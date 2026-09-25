"""Derived statistics of Cboe's VIX futures and a constant-maturity futures index built from them (Book 9, ch. 5).

Downloads the daily settlement files of the monthly VIX futures expiring from January 2013 to December 2026 from
Cboe Futures Exchange's historical data (one file per contract, named by its expiry date: the Wednesday 30 days
before the third Friday of the next month, a day earlier when that is a holiday), and the VIX index. From the
settlements (the close where early files leave the settlement at zero) it builds, for each trading day, the first
two contracts and a long index of constant maturity (one contract cycle, about a month), rebalanced daily between
them in proportion to the days left, and an inverse product that returns minus the index's daily return. It writes
only statistics: the share of days in contango (second contract above the first), the mean premium of the first
contract over VIX, the index's and the inverse's annualised returns and worst days, their values around 5 February
2018, and the index's yearly returns. Outputs in data/strategies-2: vx_summary.csv, vx_yearly.csv. Set OQB_CACHE to
a directory to keep the downloaded files between runs. Run once; the tests read the CSVs.
"""
from __future__ import annotations

import datetime as dt
import io
import os
import pathlib
import time
import urllib.error
import urllib.request

import numpy as np
import pandas as pd

UA = {"User-Agent": "OneQuantBook/1.0 (+https://one-course.com)"}
VX = "https://cdn.cboe.com/data/us/futures/market_statistics/historical_data/VX/VX_{}.csv"
VIX = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
OUT = pathlib.Path(__file__).resolve().parents[4] / "data" / "strategies-2"
CACHE = pathlib.Path(os.environ["OQB_CACHE"]) if os.environ.get("OQB_CACHE") else None


def _get(url: str) -> bytes | None:
    name = CACHE / url.rsplit("/", 1)[-1] if CACHE else None
    if name and name.exists():
        return name.read_bytes()
    time.sleep(2)
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
    except urllib.error.HTTPError:
        return None
    if name:
        CACHE.mkdir(parents=True, exist_ok=True)
        name.write_bytes(data)
    return data


def expiry(year: int, month: int) -> dt.date:
    """Wednesday 30 days before the third Friday of the following month."""
    y, m = (year + 1, 1) if month == 12 else (year, month + 1)
    first = dt.date(y, m, 1)
    friday = first + dt.timedelta(days=(4 - first.weekday()) % 7 + 14)
    return friday - dt.timedelta(days=30)


def contracts() -> dict[dt.date, pd.Series]:
    out = {}
    for y in range(2013, 2027):
        for m in range(1, 13):
            e = expiry(y, m)
            for d in (e, e - dt.timedelta(days=1)):
                raw = _get(VX.format(d.isoformat()))
                if raw:
                    df = pd.read_csv(io.BytesIO(raw))
                    df = df.set_index(pd.to_datetime(df["Trade Date"]))
                    s = df["Settle"].astype(float).where(df["Settle"] > 0, df["Close"].astype(float))
                    out[d] = s[s > 0]                   # early 2013 files leave Settle at zero: use the close
                    break
    return out


def curve(cs: dict[dt.date, pd.Series]) -> pd.DataFrame:
    """For each day: the first two contracts' settlements and the first's days to expiry and the gap to the second."""
    exps = sorted(cs)
    days = sorted(set().union(*[set(s.index) for s in cs.values()]))
    rows = []
    for d in days:
        live = [e for e in exps if pd.Timestamp(e) > d and d in cs[e].index]
        if len(live) >= 2:
            e1, e2 = live[0], live[1]
            gap = (pd.Timestamp(e2) - pd.Timestamp(e1)).days
            rows.append((d, cs[e1][d], cs[e2][d], (pd.Timestamp(e1) - d).days, gap, e1, e2))
    return pd.DataFrame(rows, columns=["date", "f1", "f2", "t1", "gap", "e1", "e2"]).set_index("date")


def index_returns(c: pd.DataFrame, cs: dict[dt.date, pd.Series]) -> pd.Series:
    """Daily return of a long position rebalanced each close to hold one contract cycle of maturity between the first
    two contracts: yesterday's weights, each contract valued today (its final settlement if it expired today)."""
    w1 = np.clip(c["t1"] / c["gap"], 0, 1)
    rets = []
    for i in range(1, len(c)):
        prev, day = c.iloc[i - 1], c.index[i]
        a = float(w1.iloc[i - 1])
        v1, v2 = cs[prev["e1"]].get(day, prev["f1"]), cs[prev["e2"]].get(day, prev["f2"])
        rets.append((a * v1 + (1 - a) * v2) / (a * prev["f1"] + (1 - a) * prev["f2"]) - 1)
    return pd.Series(rets, index=c.index[1:])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cs = contracts()
    c = curve(cs)
    vix = pd.read_csv(io.BytesIO(_get(VIX)))
    vix = vix.set_index(pd.to_datetime(vix["DATE"], format="%m/%d/%Y"))["CLOSE"].astype(float)
    r = index_returns(c, cs)
    inv = -r
    lv, li = np.log1p(r), np.log1p(inv.clip(lower=-0.999999))
    both = c.join(vix.rename("vix"), how="inner")
    rows = [("first", str(c.index[0].date())), ("last", str(c.index[-1].date())), ("days", len(c)),
            ("contango_share", float((c["f2"] > c["f1"]).mean())),
            ("f1_premium_mean", float((both["f1"] - both["vix"]).mean())),
            ("f2_f1_mean", float((c["f2"] - c["f1"]).mean())),
            ("long_ann_log", float(lv.mean() * 252)), ("long_total", float(np.expm1(lv.sum()))),
            ("long_worst", float(r.min())), ("long_worst_at", str(r.idxmin().date())),
            ("long_best", float(r.max())), ("long_best_at", str(r.idxmax().date())),
            ("inverse_ann_log", float(li.mean() * 252)), ("inverse_worst", float(inv.min())),
            ("inverse_worst_at", str(inv.idxmin().date())),
            ("vix_2018_02_02", float(vix["2018-02-02"])), ("vix_2018_02_05", float(vix["2018-02-05"])),
            ("long_2018_02_05", float(r["2018-02-05"])), ("f1_2018_02_02", float(c.loc["2018-02-02", "f1"])),
            ("f1_2018_02_05", float(c.loc["2018-02-05", "f1"])),
            ("inverse_2018_01_to_02_05", float(np.expm1(li["2018-01-02":"2018-02-05"].sum()))),
            ("inverse_2018_01_to_02_05_start", str(li["2018-01-02":].index[0].date()))]
    pd.DataFrame(rows, columns=["stat", "value"]).to_csv(OUT / "vx_summary.csv", index=False)
    yearly = lv.groupby(lv.index.year).sum()
    contango = (c["f2"] > c["f1"]).groupby(c.index.year).mean()
    vy = vix.groupby(vix.index.year)
    pd.DataFrame({"year": yearly.index, "long": np.expm1(yearly.values),
                  "inverse": np.expm1(li.groupby(li.index.year).sum().values),
                  "contango": contango.reindex(yearly.index).values,
                  "vix_change": (vy.last() / vy.first() - 1).reindex(yearly.index).values}).to_csv(
        OUT / "vx_yearly.csv", index=False)


if __name__ == "__main__":
    main()
