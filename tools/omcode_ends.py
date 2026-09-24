#!/usr/bin/env python3
"""Print the first and last line of every \\omcode range (optionally only in chapter files whose
path contains the argument), so that a range which is still in bounds but shows the wrong code
after an edit is seen (WRITING_A_QUANT_BOOK.md, section 9)."""
import glob
import re
import sys

sel = sys.argv[1] if len(sys.argv) > 1 else ""
n = 0
for tex in sorted(glob.glob("parts/**/*.tex", recursive=True)):
    if sel and sel not in tex:
        continue
    for m in re.finditer(r"\\omcode\{([^}]*)\}\{(\d+)\}\{(\d+)\}", open(tex, encoding="utf8").read()):
        path, a, b = m.group(1), int(m.group(2)), int(m.group(3))
        lines = open(path, encoding="utf8").read().splitlines()
        n += 1
        print(f"{path}:{a}-{b}\n   first: {lines[a - 1].strip()}\n   last:  {lines[b - 1].strip()}")
print(f"{n} listings")
