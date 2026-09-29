"""Build data/industry/filings_perhead.csv, the chapter's firm-year panel (run once; network for SEC company facts).

    .venv/bin/python in_panel_derive.py /path/to/scratch

Revenue after pass-through costs, in millions of the filer's currency, per filer and year 2019-2025:
  - SEC company facts (research user agent; files cached in the scratch directory, never committed), read with
    firm.filings.companyfacts: CME Group (Revenues); ICE, Nasdaq, Cboe (operating expenses + operating income, which is
    revenue less transaction-based expenses and cost of revenue); MarketAxess, Tradeweb (revenue from contracts);
    Goldman Sachs, Morgan Stanley, Interactive Brokers (net revenues);
  - Book 16's derived tables, read-only: Virtu (revenue - brokerage and clearance fees - interest and dividend expense)
    and Man Group (core net revenue - asset servicing), as Book 16, chapter 1 maps them;
  - chapter 10's table (Coinbase total revenue) and data/industry/revenue_manual.csv (hand-transcribed filers).
Headcounts: data/industry/headcounts.csv (hand-transcribed from the Forms 10-K, one quoted phrase per row).
"""
import csv
import json
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/filings"))
import firm_filings as ff  # noqa: E402

DATA = ROOT / "data/industry"
UA = "OneQuantBook research one-course.com"
CF = "https://data.sec.gov/api/xbrl/companyfacts/CIK{:010d}.json"
US = {  # firm: (CIK, kind, concepts, rule)
    "CME Group": (1156375, "exchange or venue", ["Revenues"], "first"),
    "Intercontinental Exchange": (1571949, "exchange or venue", ["OperatingExpenses", "OperatingIncomeLoss"], "sum"),
    "Nasdaq": (1120193, "exchange or venue", ["OperatingExpenses", "OperatingIncomeLoss"], "sum"),
    "Cboe Global Markets": (1374310, "exchange or venue", ["OperatingExpenses", "OperatingIncomeLoss"], "sum"),
    "MarketAxess": (1278021, "exchange or venue", ["RevenueFromContractWithCustomerExcludingAssessedTax"], "first"),
    "Tradeweb": (1758730, "exchange or venue", ["RevenueFromContractWithCustomerExcludingAssessedTax"], "first"),
    "Goldman Sachs": (886982, "bank (whole firm)", ["RevenuesNetOfInterestExpense"], "first"),
    "Morgan Stanley": (895421, "bank (whole firm)", ["RevenuesNetOfInterestExpense"], "first"),
    "Interactive Brokers": (1381197, "broker", ["RevenuesNetOfInterestExpense"], "first"),
}
LINES = {"first": "{}", "sum": "operating expenses + operating income"}
YEARS = range(2019, 2026)


def companyfacts(cik, scratch):
    p = scratch / f"cf_{cik}.json"
    if not p.exists():
        req = urllib.request.Request(CF.format(cik), headers={"User-Agent": UA, "Accept-Encoding": "identity"})
        p.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    return json.loads(p.read_text())


def us_rows(scratch):
    rows = []
    for firm, (cik, kind, concepts, rule) in US.items():
        facts = ff.companyfacts(companyfacts(cik, scratch), concepts)
        by = {}
        for f in facts:
            if f.end[5:] == "12-31" and int(f.end[:4]) in YEARS:
                by.setdefault(int(f.end[:4]), {})[f.note] = (f.value / 1e6, f.locator)
        for y, d in sorted(by.items()):
            if not all(c in d for c in concepts):
                continue
            rev = sum(d[c][0] for c in concepts)
            line = LINES[rule].format(concepts[0])
            rows.append([firm, kind, y, "USD", round(rev, 1), line,
                         f"SEC company facts CIK {cik}, accession {d[concepts[0]][1]}"])
    return rows


def desk_rows():
    rows = []
    with open(ROOT / "data/desk/filings_virtu.csv") as f:
        for r in csv.DictReader(f):
            nr = float(r["revenue"]) - float(r["brokerage_fees"]) - float(r["interest_div_expense"])
            rows.append(["Virtu Financial", "market maker", int(r["year"]), "USD", round(nr, 1),
                         "revenue - brokerage and clearance fees - interest and dividend expense",
                         "Book 16 data/desk/filings_virtu.csv"])
    with open(ROOT / "data/desk/filings_man.csv") as f:
        for r in csv.DictReader(f):
            nr = float(r["net_revenue"]) - float(r["asset_servicing"])
            rows.append(["Man Group", "asset manager", int(r["year"]), "USD", round(nr, 1),
                         "core net revenue - asset servicing", "Book 16 data/desk/filings_man.csv"])
    with open(DATA / "crypto_headcount.csv") as f:
        for r in csv.DictReader(f):
            rows.append(["Coinbase", "crypto exchange", int(r["year"]), "USD", round(float(r["revenue_m"]), 1),
                         "total revenue", "chapter 10 data/industry/crypto_headcount.csv"])
    return rows


def main(scratch):
    scratch = pathlib.Path(scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    heads = {}
    with open(DATA / "headcounts.csv") as f:
        for r in csv.DictReader(f):
            heads[(r["firm"], int(r["year"]))] = (r["employees"], r["basis"])
    out = []
    for firm, kind, y, cur, rev, line, src in us_rows(scratch) + desk_rows():
        emp, basis = heads.get((firm, y), ("", ""))
        out.append([firm, kind, y, cur, rev, emp, basis, line, src])
    with open(DATA / "revenue_manual.csv") as f:
        for r in csv.DictReader(f):
            out.append([r["firm"], r["kind"], int(r["year"]), r["currency"], r["revenue_m"], r["employees"],
                        r["basis"], r["revenue_line"], r["source"]])
    out.sort(key=lambda r: (r[1], r[0], r[2]))
    with open(DATA / "filings_perhead.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["firm", "kind", "year", "currency", "revenue_m", "employees", "basis", "revenue_line", "source"])
        w.writerows(out)


if __name__ == "__main__":
    main(sys.argv[1])
