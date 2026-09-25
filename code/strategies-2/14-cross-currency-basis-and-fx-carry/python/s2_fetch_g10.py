"""A G10 currency carry basket from public data, 2002-2025 (One Quant Book 9, chapter 14).

Downloads from FRED the month-end dollar exchange rates of nine G10 currencies (daily H.10 series, last value of
each month) and the OECD's three-month interbank rates for them and the United States (monthly). Each month, on the
previous month's rates, it ranks the nine currencies by their rate minus the US rate, is long the three highest and
short the three lowest (equal weights, against the dollar), and earns the spot change plus the rate differential for
the month. Common sample: May 2002 (the Japanese rate starts in April 2002) to December 2025 (the euro area and UK
rates end in January 2026); a rate missing for a month keeps the last value. It writes only statistics: annual
return, volatility, Sharpe ratio, skewness, worst month with date, return in September-November 2008, the parts from
carry and from spot, and how often each currency was long or short. Outputs in data/strategies-2: g10_summary.csv,
g10_monthly.csv (the basket's cumulative log return).
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
# currency: (FRED FX id, True if quoted as dollars per unit, OECD 3m interbank rate id)
CCY = {"EUR": ("DEXUSEU", True, "IR3TIB01EZM156N"), "JPY": ("DEXJPUS", False, "IR3TIB01JPM156N"),
       "GBP": ("DEXUSUK", True, "IR3TIB01GBM156N"), "CHF": ("DEXSZUS", False, "IR3TIB01CHM156N"),
       "AUD": ("DEXUSAL", True, "IR3TIB01AUM156N"), "NZD": ("DEXUSNZ", True, "IR3TIB01NZM156N"),
       "CAD": ("DEXCAUS", False, "IR3TIB01CAM156N"), "SEK": ("DEXSDUS", False, "IR3TIB01SEM156N"),
       "NOK": ("DEXNOUS", False, "IR3TIB01NOM156N")}


def _fred(sid: str) -> pd.Series:
    time.sleep(1)
    req = urllib.request.Request(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}", headers=UA)
    df = pd.read_csv(io.BytesIO(urllib.request.urlopen(req, timeout=60).read()))
    df.columns = ["date", "v"]
    return pd.to_numeric(df.set_index(pd.to_datetime(df["date"]))["v"], errors="coerce").dropna()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    us = _fred("IR3TIB01USM156N")
    spot, rate = {}, {}
    for c, (fx, per_unit, ir) in CCY.items():
        s = _fred(fx)
        s = s if per_unit else 1.0 / s                                # dollars per unit of the currency
        spot[c] = s.groupby(s.index.to_period("M")).last()
        r = _fred(ir)
        rate[c] = r.groupby(r.index.to_period("M")).last()
    spot, rate = pd.DataFrame(spot), pd.DataFrame(rate).ffill(limit=2)     # a missing month keeps the last rate
    usr = us.groupby(us.index.to_period("M")).last()
    diff = rate.sub(usr.reindex(rate.index).ffill(limit=2), axis=0).dropna()
    months = [m for m in diff.index if pd.Period("2002-05", "M") <= m <= pd.Period("2025-12", "M")]
    rows, parts = [], {"carry": [], "spot": []}
    longs, shorts = {c: 0 for c in CCY}, {c: 0 for c in CCY}
    for m in months:
        prev = m - 1
        d = diff.loc[prev]
        order = d.sort_values().index
        lo, hi = list(order[:3]), list(order[-3:])
        sp = spot.loc[m] / spot.loc[prev] - 1
        car = d / 100 / 12
        w = pd.Series(0.0, index=spot.columns)
        w[hi], w[lo] = 1 / 3, -1 / 3
        rows.append((str(m), float((w * (sp + car)).sum())))
        parts["carry"].append(float((w * car).sum()))
        parts["spot"].append(float((w * sp).sum()))
        for c in hi:
            longs[c] += 1
        for c in lo:
            shorts[c] += 1
    ret = pd.Series([x for _, x in rows], index=[m for m, _ in rows])
    dev = ret - ret.mean()
    stats = [("first", ret.index[0]), ("last", ret.index[-1]), ("months", len(ret)),
             ("ann_return", float(ret.mean() * 12)), ("ann_vol", float(ret.std() * math.sqrt(12))),
             ("sharpe", float(ret.mean() / ret.std() * math.sqrt(12))),
             ("skew", float((dev**3).mean() / (dev**2).mean() ** 1.5)), ("worst", float(ret.min())),
             ("worst_at", ret.idxmin()), ("autumn_2008", float(np.prod(1 + ret["2008-09":"2008-11"]) - 1)),
             ("carry_part", float(np.mean(parts["carry"]) * 12)), ("spot_part", float(np.mean(parts["spot"]) * 12))]
    stats += [(f"long_{c}", longs[c]) for c in CCY] + [(f"short_{c}", shorts[c]) for c in CCY]
    pd.DataFrame(stats, columns=["stat", "value"]).to_csv(OUT / "g10_summary.csv", index=False)
    pd.DataFrame({"month": ret.index, "cum_log": np.cumsum(np.log1p(ret.to_numpy()))}).to_csv(
        OUT / "g10_monthly.csv", index=False)


if __name__ == "__main__":
    main()
