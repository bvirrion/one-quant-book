"""Provenance script (network; not run by the tests): builds data/research/payrolls_realtime.csv and
data/research/payrolls_vintages_2008_2009.csv from the Federal Reserve Bank of Philadelphia's Real-Time
Data Set for Macroeconomists, nonfarm payroll employment (EMPLOY), monthly vintages.

Vintage EMPLOYyyMmm holds the history as published in the BLS Employment Situation report of that
month. The monthly change of month m in a vintage is level(m) - level(m - 1) in that vintage. The
first release of m is the first vintage in which both levels appear (normally m + 1; later when a
report was delayed, as for September 2025).

    python3 rs_fetch_payrolls.py [path/to/employmvmd.xlsx]
"""
from __future__ import annotations

import pathlib
import re
import sys
import urllib.request
import zipfile

URL = ("https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/real-time-data/"
       "data-files/xlsx/employmvmd.xlsx")
OUT = pathlib.Path(__file__).resolve().parents[4] / "data" / "research"


def _col(s: str) -> int:
    n = 0
    for ch in s:
        n = n * 26 + ord(ch) - 64
    return n


def read_matrix(path):
    """(vintages {(y, m): col}, observations {(y, m): row}, cells {row: {col: text}})."""
    z = zipfile.ZipFile(path)
    ss = re.findall(r"<si>(?:<t[^>]*>(.*?)</t>|<r>.*?</r>)</si>", z.read("xl/sharedStrings.xml").decode())
    sheet = z.read("xl/worksheets/sheet1.xml").decode()
    rows = {}
    for m in re.finditer(r'<row r="(\d+)"[^>]*>(.*?)</row>', sheet, re.S):
        cells = {}
        for c in re.finditer(r'<c r="([A-Z]+)\d+"([^>]*?)(?:/>|>(.*?)</c>)', m.group(2), re.S):
            v = re.search(r"<v>(.*?)</v>", c.group(3) or "")
            if v:
                cells[_col(c.group(1))] = ss[int(v.group(1))] if 't="s"' in c.group(2) else v.group(1)
        rows[int(m.group(1))] = cells
    vint = {}
    for col, h in rows.pop(1).items():
        mm = re.match(r"EMPLOY(\d\d)M(\d+)", h)
        if mm:
            yy = int(mm.group(1))
            vint[(1900 + yy if yy >= 64 else 2000 + yy, int(mm.group(2)))] = col
    obs = {tuple(int(x) for x in cells[1].split(":")): r for r, cells in rows.items()}
    return vint, obs, rows


def shift(ym, k):
    y, m = ym
    m += k
    y, m = y + (m - 1) // 12, (m - 1) % 12 + 1
    return (y, m)


def build(path):
    vint, obs, rows = read_matrix(path)

    def level(o, v):
        try:
            return float(rows[obs[o]][vint[v]])
        except (KeyError, ValueError):
            return None

    def change(o, v):
        a, b = level(o, v), level(shift(o, -1), v)
        return None if a is None or b is None else a - b

    latest = max(vint)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "payrolls_realtime.csv", "w") as f:
        f.write("month,first_vintage,first,second,third,latest,latest_vintage\n")
        o = (2000, 1)
        while o <= shift(latest, -2):
            v1 = next((v for v in (shift(o, k) for k in range(1, 6)) if change(o, v) is not None), None)
            vals = [change(o, shift(v1, k)) for k in range(3)] if v1 else [None] * 3
            txt = ["" if x is None else f"{x:.0f}" for x in vals]
            f.write(f"{o[0]}-{o[1]:02d},{'' if v1 is None else f'{v1[0]}-{v1[1]:02d}'},{','.join(txt)},"
                    f"{change(o, latest):.0f},{latest[0]}-{latest[1]:02d}\n")
            o = shift(o, 1)
    with open(OUT / "payrolls_vintages_2008_2009.csv", "w") as f:
        f.write("month,vintage,change\n")
        o = (2008, 1)
        while o <= (2009, 12):
            for k in range(1, 37):
                c = change(o, shift(o, k))
                if c is not None:
                    v = shift(o, k)
                    f.write(f"{o[0]}-{o[1]:02d},{v[0]}-{v[1]:02d},{c:.0f}\n")
            o = shift(o, 1)


if __name__ == "__main__":
    src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else OUT / "employmvmd.xlsx"
    if not src.exists():
        urllib.request.urlretrieve(URL, src)
    build(src)
