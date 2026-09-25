"""The dollar at month-end against the S&P 500's month, 1999-2026 (One Quant Book 9, chapter 15).

Downloads from FRED the Board's H.10 daily noon New York exchange rates for six currencies (euro, sterling, yen,
Swiss franc, Australian and Canadian dollars) and from Cboe the S&P 500 index history, and forms a log dollar index
(the average log price of the dollar in the six). For each month from January 1999 with at least 15 common days it
takes the S&P 500's log return from the month's first day to k + 1 days before its end, and the dollar index's log
change over the month's last k days, for k = 2, 3, 5. It writes only statistics: for each k, the number of months,
the regression slope and correlation of the dollar's change on the S&P return with its t-statistic, and the mean
(basis points) and t-statistic of a trade that sells the dollar over the last k days when the S&P has risen and buys
it when it has fallen. Output in data/strategies-2: monthend_summary.csv. Run once.
"""
from __future__ import annotations

import io
import math
import pathlib
import time
import urllib.request

import numpy as np
import pandas as pd

UA = {"User-Agent": "OneQuantBook/1.0 (+https://one-course.com)"}
OUT = pathlib.Path(__file__).resolve().parents[4] / "data" / "strategies-2"
FX = (("DEXUSEU", True), ("DEXUSUK", True), ("DEXJPUS", False), ("DEXSZUS", False), ("DEXUSAL", True),
      ("DEXCAUS", False))


def _get(url: str) -> bytes:
    time.sleep(1)
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    usd = {}
    for sid, per_unit in FX:
        df = pd.read_csv(io.BytesIO(_get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}")))
        df.columns = ["date", "v"]
        s = pd.to_numeric(df.set_index(pd.to_datetime(df["date"]))["v"], errors="coerce").dropna()
        usd[sid] = 1 / s if per_unit else s                            # foreign units per dollar: the dollar's price
    dollar = np.log(pd.DataFrame(usd).dropna()).mean(axis=1)
    sp = pd.read_csv(io.BytesIO(_get("https://cdn.cboe.com/api/global/us_indices/daily_prices/SPX_History.csv")))
    sp = sp.set_index(pd.to_datetime(sp["DATE"], format="%m/%d/%Y"))[sp.columns[-1]].astype(float)
    df = pd.concat([dollar.rename("usd"), np.log(sp).rename("spx")], axis=1).dropna()
    df = df[df.index >= "1999-01-01"]
    rows = [("first", str(df.index[0].date())), ("last", str(df.index[-1].date()))]
    for k in (2, 3, 5):
        sig, resp = [], []
        for _, g in df.groupby(df.index.to_period("M")):
            if len(g) >= 15:
                sig.append(g["spx"].iloc[-k - 1] - g["spx"].iloc[0])
                resp.append(g["usd"].iloc[-1] - g["usd"].iloc[-k - 1])
        sig, resp = np.array(sig), np.array(resp)
        c, n = float(np.corrcoef(sig, resp)[0, 1]), len(sig)
        trade = -np.sign(sig) * resp
        rows += [(f"k{k}_months", n), (f"k{k}_slope", float(np.polyfit(sig, resp, 1)[0])), (f"k{k}_corr", c),
                 (f"k{k}_t", c * math.sqrt(n - 2) / math.sqrt(1 - c * c)),
                 (f"k{k}_trade_bp", float(trade.mean() * 1e4)),
                 (f"k{k}_trade_t", float(trade.mean() / trade.std(ddof=1) * math.sqrt(n)))]
    pd.DataFrame(rows, columns=["stat", "value"]).to_csv(OUT / "monthend_summary.csv", index=False)


if __name__ == "__main__":
    main()
