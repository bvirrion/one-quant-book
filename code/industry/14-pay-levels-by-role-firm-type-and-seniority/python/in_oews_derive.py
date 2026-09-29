"""Derive data/industry/oews_finance.csv from BLS OEWS May 2025 national industry-specific estimates (run once).

    .venv/bin/python in_oews_derive.py /path/to/oesm25in4/nat4d_M2025_dl.xlsx

Keeps two industries (523000 securities, commodity contracts and other financial investments; 5220A1 credit
intermediation, 5221 and 5223) and eight occupations; wage percentiles are annual US dollars; a '#' (top-coded) or
'*' (not available) cell is kept as text.
"""
import csv
import pathlib
import sys

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[4]
NAICS = {"523000": "securities and investments", "5220A1": "credit intermediation (banks)"}
OCC = ("00-0000", "11-3031", "13-2051", "13-2099", "15-1252", "15-2041", "15-2051", "41-3031")
COLS = ("TOT_EMP", "A_PCT10", "A_PCT25", "A_MEDIAN", "A_PCT75", "A_PCT90", "A_MEAN")


def main(path):
    wb = openpyxl.load_workbook(path, read_only=True)
    rows = wb.worksheets[0].iter_rows(values_only=True)
    h = next(rows)
    out = []
    for r in rows:
        d = dict(zip(h, r, strict=False))
        if d["NAICS"] in NAICS and d["OCC_CODE"] in OCC:
            out.append([d["NAICS"], NAICS[d["NAICS"]], d["OCC_CODE"], d["OCC_TITLE"]] + [d[c] for c in COLS])
    wb.close()
    with open(ROOT / "data/industry/oews_finance.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["naics", "industry", "occ", "occupation", "employment", "p10", "p25", "p50", "p75", "p90", "mean"])
        w.writerows(sorted(out))


if __name__ == "__main__":
    main(sys.argv[1])
