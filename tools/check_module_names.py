#!/usr/bin/env python3
"""Every importable Python module under code/ (teaching modules in */python/ and firm_*.py) must have a
name unique in the repository: all tests run in one pytest session, and two modules of the same name
shadow each other on sys.path (Book 2, chapter 4, collided with Book 1, chapter 24)."""
import collections
import pathlib
import sys

names = collections.defaultdict(list)
for p in pathlib.Path("code").rglob("*.py"):
    if "tests" in p.parts or p.name.startswith("fig_") or "target" in p.parts:
        continue
    names[p.name].append(str(p))
dups = {k: v for k, v in names.items() if len(v) > 1}
for k, v in sorted(dups.items()):
    print(f"DUPLICATE {k}: {', '.join(v)}")
print(f"{sum(len(v) for v in names.values())} modules checked, {len(dups)} duplicate names")
sys.exit(1 if dups else 0)
