"""Leveraged funds' positions in Treasury futures from the CFTC's Traders in Financial Futures (Book 9, ch. 11).

Downloads the CFTC's yearly Traders in Financial Futures (futures only) files from 2010 to 2026 and keeps the six
CBOT Treasury futures by contract code (2-year 042601, 5-year 044601, 10-year 043602, Ultra 10-year 043607, bond
020601, Ultra bond 020604). For each weekly report it writes the leveraged funds' net position (long minus short) in
notional face value, in billions of dollars ($200,000 a contract for the 2-year, $100,000 for the others), in total
and by contract, and statistics: the largest net short and its date, the value on 18 February and 17 March 2020, and
the last. Outputs in data/strategies-2: tff_levfunds.csv (weekly aggregate), tff_summary.csv. Set OQB_CACHE to keep
the zip files between runs. Run once.
"""
from __future__ import annotations

import io
import os
import pathlib
import time
import urllib.error
import urllib.request
import zipfile

import pandas as pd

UA = {"User-Agent": "OneQuantBook/1.0 (+https://one-course.com)"}
URL = "https://www.cftc.gov/files/dea/history/fut_fin_txt_{}.zip"
CODES = {"042601": ("2y", 200_000), "044601": ("5y", 100_000), "043602": ("10y", 100_000),
         "043607": ("ultra10y", 100_000), "020601": ("bond", 100_000), "020604": ("ultrabond", 100_000)}
OUT = pathlib.Path(__file__).resolve().parents[4] / "data" / "strategies-2"
CACHE = pathlib.Path(os.environ["OQB_CACHE"]) if os.environ.get("OQB_CACHE") else None


def _get(year: int) -> bytes | None:
    name = CACHE / f"fut_fin_txt_{year}.zip" if CACHE else None
    if name and name.exists():
        return name.read_bytes()
    time.sleep(2)
    try:
        data = urllib.request.urlopen(urllib.request.Request(URL.format(year), headers=UA), timeout=120).read()
    except urllib.error.HTTPError:
        return None
    if name:
        CACHE.mkdir(parents=True, exist_ok=True)
        name.write_bytes(data)
    return data


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frames = []
    for year in range(2010, 2027):
        raw = _get(year)
        if raw is None:
            continue
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), dtype={"CFTC_Contract_Market_Code": str,
                                                             "As_of_Date_In_Form_YYMMDD": str}, low_memory=False)
        df["CFTC_Contract_Market_Code"] = df["CFTC_Contract_Market_Code"].str.strip()   # older files pad codes
        df = df[df["CFTC_Contract_Market_Code"].isin(CODES)]
        frames.append(df[["As_of_Date_In_Form_YYMMDD", "CFTC_Contract_Market_Code", "Lev_Money_Positions_Long_All",
                          "Lev_Money_Positions_Short_All"]])
    df = pd.concat(frames).drop_duplicates()
    df["date"] = pd.to_datetime(df["As_of_Date_In_Form_YYMMDD"].str.strip().str.zfill(6), format="%y%m%d")
    face = df["CFTC_Contract_Market_Code"].map(lambda c: CODES[c][1])
    df["net_bn"] = (df["Lev_Money_Positions_Long_All"] - df["Lev_Money_Positions_Short_All"]) * face / 1e9
    df["contract"] = df["CFTC_Contract_Market_Code"].map(lambda c: CODES[c][0])
    wide = df.pivot_table(index="date", columns="contract", values="net_bn", aggfunc="sum").sort_index()
    wide["total"] = wide.sum(axis=1)
    wide.round(2).to_csv(OUT / "tff_levfunds.csv")
    t = wide["total"]
    near = lambda d: float(t[t.index <= d].iloc[-1])                 # noqa: E731
    rows = [("first", str(t.index[0].date())), ("last", str(t.index[-1].date())), ("weeks", len(t)),
            ("min", float(t.min())), ("min_at", str(t.idxmin().date())), ("2020-02-18", near("2020-02-18")),
            ("2020-03-17", near("2020-03-17")), ("2017-12-26", near("2017-12-26")), ("last_value", float(t.iloc[-1])),
            ("mean_2010_2014", float(t["2010":"2014"].mean()))]
    pd.DataFrame(rows, columns=["stat", "value"]).to_csv(OUT / "tff_summary.csv", index=False)


if __name__ == "__main__":
    main()
