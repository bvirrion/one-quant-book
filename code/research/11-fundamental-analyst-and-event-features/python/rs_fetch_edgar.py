"""Point-in-time earnings data from SEC EDGAR (One Quant Book 7, chapter 11).

For ten large US companies, downloads from the public data.sec.gov APIs (no key; the SEC asks for a descriptive
User-Agent and at most ten requests a second): the diluted earnings per share reported in XBRL, with every filing that
reported each value (companyfacts), and the filing calendar (submissions): 10-Q and 10-K filings with their period ends,
and 8-K filings with item 2.02 (results of operations), the earnings releases. Writes
data/research/edgar_eps.csv and data/research/edgar_filings.csv (US Government works, public domain). Run once; the
chapter's tests read the CSVs.
"""
from __future__ import annotations

import csv
import json
import pathlib
import time
import urllib.request

UA = {"User-Agent": "OneQuantBook/1.0 (+https://one-course.com)"}
OUT = pathlib.Path(__file__).resolve().parents[4] / "data" / "research"
FIRMS = {320193: "Apple", 789019: "Microsoft", 104169: "Walmart", 21344: "Coca-Cola", 200406: "Johnson & Johnson",
         34088: "Exxon Mobil", 80424: "Procter & Gamble", 50863: "Intel", 354950: "Home Depot", 320187: "Nike"}
SINCE = "2012-01-01"


def get(url: str) -> dict:
    time.sleep(0.2)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def filings(cik: int) -> list[dict]:
    """All filings since SINCE: the recent block and the older pages the submissions file points to."""
    sub = get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
    blocks = [sub["filings"]["recent"]]
    for f in sub["filings"].get("files", []):
        if f["filingTo"] >= SINCE:
            blocks.append(get(f"https://data.sec.gov/submissions/{f['name']}"))
    rows = []
    for b in blocks:
        for i, form in enumerate(b["form"]):
            if b["filingDate"][i] < SINCE:
                continue
            if form in ("10-Q", "10-K") or (form == "8-K" and "2.02" in b["items"][i]):
                rows.append({"cik": cik, "form": form, "filed": b["filingDate"][i], "period": b["reportDate"][i],
                             "accepted": b["acceptanceDateTime"][i], "accn": b["accessionNumber"][i]})
    return rows


def eps(cik: int) -> list[dict]:
    facts = get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")["facts"]["us-gaap"]
    out = []
    for f in facts["EarningsPerShareDiluted"]["units"]["USD/shares"]:
        if f["filed"] >= SINCE and f["form"] in ("10-Q", "10-K", "10-Q/A", "10-K/A"):
            out.append({"cik": cik, "start": f["start"], "end": f["end"], "val": f["val"], "form": f["form"],
                        "fy": f["fy"], "fp": f["fp"], "filed": f["filed"], "accn": f["accn"]})
    return out


def main() -> None:
    fl, ep = [], []
    for cik in FIRMS:
        fl += filings(cik)
        ep += eps(cik)
    for name, rows in (("edgar_filings.csv", fl), ("edgar_eps.csv", ep)):
        with open(OUT / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(sorted(rows, key=lambda r: (r["cik"], r["filed"], r["accn"])))


if __name__ == "__main__":
    main()
