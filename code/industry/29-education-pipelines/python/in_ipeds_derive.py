"""Derive data/industry/ipeds_completions.csv from the IPEDS completions files (run once; raw zips not committed).

    .venv/bin/python in_ipeds_derive.py /path/to/dir     # holding C2010_A.zip, C2014_A.zip, C2019_A.zip, C2024_A.zip

Awards (first majors) by year, CIP code and level (bachelor 5, master 7, research doctorate 17) for financial
mathematics (27.0305), financial analytics (30.7104, new in CIP 2020), statistics (27.0501), mathematics (27.0101),
computer science (11.0701) and physics (40.0801). NCES data are US government works (public domain).
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/edupipe"))
import firm_edupipe as fe  # noqa: E402

YEARS = (2010, 2014, 2019, 2024)
CIPS = {"27.0305": "financial mathematics", "30.7104": "financial analytics", "27.0501": "statistics",
        "27.0101": "mathematics", "11.0701": "computer science", "40.0801": "physics"}
LEVELS = ("5", "7", "17")


def main(folder):
    rows = []
    for y in YEARS:
        got = fe.read_ipeds(pathlib.Path(folder) / f"C{y}_A.zip", CIPS, LEVELS)
        for cip in CIPS:
            for lvl in LEVELS:
                rows.append((y, cip, CIPS[cip], fe.LEVELS[lvl], got.get((cip, lvl), 0)))
    with open(ROOT / "data/industry/ipeds_completions.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["year", "cip", "field", "level", "awards"])
        w.writerows(rows)


if __name__ == "__main__":
    main(sys.argv[1])
