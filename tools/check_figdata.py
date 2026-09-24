#!/usr/bin/env python3
"""Every CSV under figdata/ must have the same number of comma-separated fields on every line:
a comma inside a label silently shifts pgfplots columns (or stops the build)."""
import glob
import sys

bad = 0
files = sorted(glob.glob("figdata/**/*.csv", recursive=True))
for path in files:
    rows = [ln.rstrip("\n") for ln in open(path, encoding="utf8") if ln.strip()]
    n = rows[0].count(",")
    for i, ln in enumerate(rows[1:], start=2):
        if ln.count(",") != n:
            print(f"COLUMNS  {path}:{i}: {ln.count(',') + 1} fields, header has {n + 1}")
            bad += 1
print(f"{len(files)} chart CSVs checked, {bad} problems")
sys.exit(1 if bad else 0)
