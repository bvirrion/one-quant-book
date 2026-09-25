"""Derived statistics of the S&P 500 and its short-dated implied vol around FOMC statements (One Quant Book 9, ch. 4).

Reads the Federal Reserve's FOMC meeting calendars (historical pages 2011-2020 and the current page) and keeps the
scheduled meetings (not unscheduled, cancelled or notation votes), dated by their last day, the day of the statement,
from January 2011 (the first year of VIX9D) to 22 September 2026. Downloads Cboe's daily histories of the S&P 500
(SPX), VIX and the 9-day VIX (VIX9D) and writes only statistics: the number of statement days, the mean absolute
and mean squared log return of the S&P 500 on statement days and on other days, the share of statement days on
which VIX9D and VIX fell, and their mean log changes on statement days and other days. Outputs in
data/strategies-2: fomc_summary.csv and fomc_dates.csv (the statement dates, public facts). Run once; the tests
read the CSVs.
"""
from __future__ import annotations

import io
import pathlib
import re
import time
import urllib.request

import numpy as np
import pandas as pd

UA = {"User-Agent": "OneQuantBook/1.0 (+https://one-course.com)"}
FED = "https://www.federalreserve.gov/monetarypolicy/"
CBOE = "https://cdn.cboe.com/api/global/us_indices/daily_prices/"
OUT = pathlib.Path(__file__).resolve().parents[4] / "data" / "strategies-2"
MONTHS = {m: i + 1 for i, m in enumerate(("January", "February", "March", "April", "May", "June", "July", "August",
                                          "September", "October", "November", "December"))}
SHORT = {m[:3]: i for m, i in MONTHS.items()}
SKIP = ("unscheduled", "cancelled", "notation", "conference")


def _get(url: str) -> bytes:
    time.sleep(3)
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()


def _date(year: int, month: str, days: str) -> pd.Timestamp:
    """Last day of a meeting: 'Apr/May' with '30-1' ends on 1 May."""
    m = SHORT[month.split("/")[-1][:3]]
    return pd.Timestamp(year, m, int(re.findall(r"\d+", days)[-1]))


def meetings() -> list[pd.Timestamp]:
    out = []
    for y in range(2011, 2021):
        html = _get(FED + f"fomchistorical{y}.htm").decode("utf-8", "ignore")
        for head in re.findall(r'panel-heading--shaded">([^<]*)', html):
            if "Meeting" in head and not any(k in head.lower() for k in SKIP):
                month, days = head.split()[0], head.split()[1]
                out.append(_date(y, month, days))
    html = _get(FED + "fomccalendars.htm").decode("utf-8", "ignore")
    parts = re.split(r'<h4><a id="\d+">(\d{4}) FOMC Meetings</a></h4>', html)
    for i in range(1, len(parts), 2):
        pairs = re.findall(r'fomc-meeting__month[^>]*><strong>([^<]*)</strong>.*?fomc-meeting__date[^>]*>([^<]*)<',
                           parts[i + 1], re.S)
        for month, days in pairs:
            if not any(k in days.lower() for k in SKIP):
                out.append(_date(int(parts[i]), month, days))
    return sorted(d for d in set(out) if d <= pd.Timestamp("2026-09-22"))


def _cboe(name: str) -> pd.Series:
    df = pd.read_csv(io.BytesIO(_get(CBOE + f"{name}_History.csv")))
    df["DATE"] = pd.to_datetime(df["DATE"], format="%m/%d/%Y")
    col = "CLOSE" if "CLOSE" in df.columns else name
    x = df.set_index("DATE")[col].astype(float)
    return x[x > 0]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    days = pd.DatetimeIndex(meetings())
    px = pd.concat({n: np.log(_cboe(n)) for n in ("SPX", "VIX", "VIX9D")}, axis=1).dropna().diff().dropna()
    px = px[px.index >= "2011-01-01"]
    ev = px.index.isin(days)
    rows = [("statement_days", int(ev.sum())), ("other_days", int((~ev).sum())),
            ("first", str(px.index[ev][0].date())), ("last", str(px.index[ev][-1].date())),
            ("spx_abs_event", float(px["SPX"][ev].abs().mean())), ("spx_abs_other", float(px["SPX"][~ev].abs().mean())),
            ("spx_sq_event", float((px["SPX"][ev] ** 2).mean())), ("spx_sq_other", float((px["SPX"][~ev] ** 2).mean()))]
    for n in ("VIX9D", "VIX"):
        rows += [(f"{n.lower()}_fell_event", float((px[n][ev] < 0).mean())),
                 (f"{n.lower()}_fell_other", float((px[n][~ev] < 0).mean())),
                 (f"{n.lower()}_chg_event", float(px[n][ev].mean())),
                 (f"{n.lower()}_chg_other", float(px[n][~ev].mean()))]
    pd.DataFrame(rows, columns=["stat", "value"]).to_csv(OUT / "fomc_summary.csv", index=False)
    pd.DataFrame({"date": [str(d.date()) for d in days]}).to_csv(OUT / "fomc_dates.csv", index=False)


if __name__ == "__main__":
    main()
