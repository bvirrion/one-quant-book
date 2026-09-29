"""Derive data/industry/oews_roles.csv from BLS OEWS May 2025 national estimates (run once; used by chapters 18-25).

    .venv/bin/python in_oews_roles_derive.py /path/to/oesm25in4

Reads nat4d_M2025_dl.xlsx (four-digit industries) and natsector_M2025_dl.xlsx (sectors 51, 52, 54), streamed read-only,
and keeps the occupations of Part III's roles in the industries that employ them. Wage percentiles are annual US
dollars; a '#' (at or above the survey's top code) or '*' (not available) cell is kept as text. Occupation-by-industry
estimates only: no employer, no person.
"""
import csv
import pathlib
import sys

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[4]
NAICS = {"523000": "securities and investments", "5220A1": "credit intermediation (banks)",
         "525900": "other investment pools and funds", "524100": "insurance carriers",
         "513200": "software publishers", "518200": "computing infrastructure and data processing",
         "519200": "web search portals and other information", "541500": "computer systems design",
         "541700": "scientific research and development", "551100": "management of companies",
         "51": "information (sector)", "52": "finance and insurance (sector)",
         "54": "professional scientific and technical services (sector)"}
OCC = ("00-0000", "11-1011", "11-1021", "11-3021", "11-3031", "13-1041", "13-1111", "13-2011", "13-2041", "13-2051",
       "13-2054", "13-2099", "15-1211", "15-1212", "15-1241", "15-1242", "15-1244", "15-1252", "15-1253", "15-1299",
       "15-2031", "15-2041", "15-2051", "23-1011", "41-3031", "43-4011")
COLS = ("TOT_EMP", "A_PCT10", "A_PCT25", "A_MEDIAN", "A_PCT75", "A_PCT90", "A_MEAN")
FILES = ("nat4d_M2025_dl.xlsx", "natsector_M2025_dl.xlsx")


def rows(path):
    wb = openpyxl.load_workbook(path, read_only=True)
    try:
        it = wb.worksheets[0].iter_rows(values_only=True)
        h = next(it)
        for r in it:
            d = dict(zip(h, r, strict=False))
            if str(d["NAICS"]) in NAICS and d["OCC_CODE"] in OCC and str(d.get("OWN_CODE", "5")) in ("5", "1235"):
                yield [str(d["NAICS"]), NAICS[str(d["NAICS"])], d["OCC_CODE"], d["OCC_TITLE"]] + [d[c] for c in COLS]
    finally:
        wb.close()


def main(folder):
    out = []
    for name in FILES:
        out.extend(rows(pathlib.Path(folder) / name))
    with open(ROOT / "data/industry/oews_roles.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["naics", "industry", "occ", "occupation", "employment", "p10", "p25", "p50", "p75", "p90", "mean"])
        w.writerows(sorted(out))


if __name__ == "__main__":
    main(sys.argv[1])
