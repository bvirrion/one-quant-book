#!/usr/bin/env python3
"""Every CSV under figdata/ must have the same number of comma-separated fields on every line:
a comma inside a label silently shifts pgfplots columns (or stops the build). No field may hold a
'%' (pgfplots reads it as a comment and silently drops the rest of the row) or an unpaired '$'
(it opens math mode for the rest of the label); write "pct" and "USD" instead. A paired math label
such as $t = 0.8$ is fine (Books 14 and 16, 2026-09-28)."""
import glob
import sys

bad = 0
files = sorted(glob.glob("figdata/**/*.csv", recursive=True))
for path in files:
    rows = [ln.rstrip("\n") for ln in open(path, encoding="utf8") if ln.strip()]
    if len(rows) < 2:  # empty, or header only: nothing for pgfplots to draw
        print(f"EMPTY    {path}: {len(rows)} line(s)")
        bad += 1
        continue
    n = rows[0].count(",")
    for i, ln in enumerate(rows, start=1):
        if "%" in ln or any(f.count("$") % 2 for f in ln.split(",")):
            print(f"CHAR     {path}:{i}: '%' or an unpaired '$' in a field")
            bad += 1
    for i, ln in enumerate(rows[1:], start=2):
        if ln.count(",") != n:
            print(f"COLUMNS  {path}:{i}: {ln.count(',') + 1} fields, header has {n + 1}")
            bad += 1
print(f"{len(files)} chart CSVs checked, {bad} problems")
sys.exit(1 if bad else 0)
