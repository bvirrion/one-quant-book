"""Derive the platform panel from several SEC adviser files (run once; raw files are not committed).

    .venv/bin/python in_platform_derive.py file1.zip file2.zip ...

Writes data/industry/adv_platforms.csv: one row per (file date, platform adviser): employees, advisory employees,
RAUM in $ billion. Advisers are matched by CRD number, which does not change when a firm renames itself.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/formadv"))
import firm_formadv as fa  # noqa: E402

PLATFORMS = {"158117": ("Millennium Management", "F2"), "138111": ("Balyasny Asset Management", "F3"),
             "281984": ("Schonfeld Strategic Advisors", "F4"), "294156": ("ExodusPoint Capital Management", "F5")}


def file_date(path):
    m = re.search(r"ia(\d{2})(\d{2})(\d{2})", pathlib.Path(path).name)
    mm, dd, yy = m.groups()
    return f"20{yy}-{mm}"


def main(paths):
    rows = []
    for p in paths:
        for a in fa.read(p, hedge_only=False):
            if a.crd in PLATFORMS:
                lab, led = PLATFORMS[a.crd]
                rows.append((file_date(p), lab, a.employees, a.advisory, (a.raum or 0) / 1e9, led))
    with open(ROOT / "data/industry/adv_platforms.csv", "w") as f:
        f.write("file,platform,employees,advisory,raum_bn,ledger\n")
        for r in sorted(rows):
            f.write(f"{r[0]},{r[1]},{r[2]:.0f},{r[3]:.0f},{r[4]:.2f},{r[5]}\n")


if __name__ == "__main__":
    main(sys.argv[1:])
