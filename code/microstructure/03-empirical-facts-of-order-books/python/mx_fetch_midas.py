"""Fetch the SEC's MIDAS market-structure data (US government work, public domain) and write the derived statistics
the chapter uses to data/microstructure/ (network needed; not run by the tests). www.sec.gov refuses scripted requests
whose user agent carries no contact e-mail, and no personal e-mail is ever sent (user rule, 2026-09-29), so this script
may be refused; the derived CSVs it once wrote are committed and are what the chapter and its tests read.

    .venv/bin/python code/microstructure/03-empirical-facts-of-order-books/python/mx_fetch_midas.py

midas_lifetimes.csv  cumulative share of cancelled (and of executed) orders gone within 1 ms ... 1 min, by market
                     capitalisation group of stocks, 2026 Q2 (Hazards and Survivors by Time Period)
midas_yearly.csv     yearly means of the daily stock cancel-to-trade ratio, trade-to-order volume, hidden rate and
                     odd-lot rate, all exchanges (Summary Metrics by Exchange, 2012 - June 2026)
"""
import csv
import io
import pathlib
import urllib.request
import zipfile

import numpy as np

UA = {"User-Agent": "One Quant Book research"}  # no personal contact, ever (user rule, 2026-09-29)
BASE = "https://www.sec.gov/files/opa/data/market-structure/"
OUT = pathlib.Path(__file__).resolve().parents[4] / "data" / "microstructure"
POINTS = [("1ms", 1e-3), ("10ms", 1e-2), ("100ms", 0.1), ("1s", 1.0), ("10s", 10.0), ("1min", 60.0)]


def fetch(path: str) -> zipfile.ZipFile:
    with urllib.request.urlopen(urllib.request.Request(BASE + path, headers=UA), timeout=120) as r:
        return zipfile.ZipFile(io.BytesIO(r.read()))


def cdf_at(z: zipfile.ZipFile, name: str) -> list[float]:
    rows = list(csv.DictReader(io.TextIOWrapper(z.open(name))))
    x = np.array([float(r["xaxis"]) for r in rows]) * 60.0          # the files' axis is in minutes
    c = np.array([float(r["cdf"]) if r["cdf"] else 0.0 for r in rows])
    return [float(np.interp(t, x, c)) for _, t in POINTS]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    z = fetch("hazards-survivors-time-period/haz_sur_q2_2026.zip")
    with open(OUT / "midas_lifetimes.csv", "w") as f:
        f.write("group,event," + ",".join(p for p, _ in POINTS) + "\n")
        for g in ("large", "mid", "small"):
            for ev in ("cancel", "trade"):
                v = cdf_at(z, f"files/{g}_s_{ev}surv.csv")
                f.write(f"{g},{ev}," + ",".join(f"{x:.4f}" for x in v) + "\n")
    z = fetch("summary-metrics-exchange/metrics_by_exchange_q2_2026.zip")
    rows = list(csv.DictReader(io.TextIOWrapper(z.open("etp_stock_timeseries3.csv"))))
    cols = ["Stock Cancel-Trade Ratio", "Stock Trade-Order Volume", "Stock Hidden Rate", "Stock Oddlot Rate"]
    years: dict[str, list] = {}
    for r in rows:
        years.setdefault(r["Date"][:4], []).append([float(r[c]) for c in cols])
    with open(OUT / "midas_yearly.csv", "w") as f:
        f.write("year,cancel_to_trade,trade_to_order_volume,hidden_rate,oddlot_rate,days\n")
        for y, v in sorted(years.items()):
            m = np.mean(v, axis=0)
            f.write(f"{y},{m[0]:.2f},{m[1]:.3f},{m[2]:.2f},{m[3]:.2f},{len(v)}\n")


if __name__ == "__main__":
    main()
