"""Re-pull the chapter's machine-readable filings and rewrite their snapshot files (network; never run by the tests).

    .venv/bin/python in_fetch.py /path/to/scratch

Downloads into the scratch directory (never committed): Quadrature Capital Limited's inline-XBRL accounts for the year
ended 31 January 2025 from Companies House, and Virtu Financial's XBRL company facts from SEC EDGAR (declared research
user agent, one request). Parses both with firm.filings and writes data/industry/filings_snapshot/quadrature_ixbrl.csv
and virtu.csv. The image-only filings are transcribed by hand in the other snapshot files, each row with its page.
"""
import json
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/filings"))
import firm_filings as ff  # noqa: E402

OUT = ROOT / "data/industry/filings_snapshot"
CH = "https://find-and-update.company-information.service.gov.uk/company/"
QUAD = CH + "09516131/filing-history/MzQ4NDg0MjIyMGFkaXF6a2N4/document?format=xhtml&download=1"
VIRT = "https://data.sec.gov/api/xbrl/companyfacts/CIK0001592386.json"
UA_BROWSER = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
UA_RESEARCH = "OneQuantBook research one-course.com"
KEEP = ("Revenue", "AdministrativeExpenses", "OtherOperatingIncome", "OperatingProfit", "ProfitBeforeTax",
        "ProfitAfterTax", "StaffCosts", "WagesSalaries", "SocialSecurityCosts", "PensionCosts", "AverageEmployees",
        "DividendsPaid")
VIRTU = ("Revenues", "TradingGainsLosses", "LaborAndRelatedExpense")


def fetch(url, path, ua):
    if not path.exists():
        req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Encoding": "identity"})
        path.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    return path


def main(scratch):
    scratch = pathlib.Path(scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    text = fetch(QUAD, scratch / "09516131_20250131.xhtml", UA_BROWSER).read_text(errors="ignore")
    facts = [f for f in ff.parse_ixbrl(text, "Quadrature Capital Limited", QUAD)
             if f.concept in KEEP and not f.dims and f.start]
    ff.Snapshot(facts).save(OUT / "quadrature_ixbrl.csv")
    doc = json.loads(fetch(VIRT, scratch / "companyfacts_1592386.json", UA_RESEARCH).read_text())
    facts = [f for f in ff.companyfacts(doc, VIRTU, "Virtu Financial Inc.", VIRT) if f.end >= "2020-12-31"]
    ff.Snapshot(facts).save(OUT / "virtu.csv")


if __name__ == "__main__":
    main(sys.argv[1])
