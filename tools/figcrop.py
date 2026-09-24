#!/usr/bin/env python3
"""tools/figcrop.py "<first words of a caption>" out.png [height_pt]

Book 1 by default; OQB_BOOK=2 tools/figcrop.py ... for another book.

Finds the page and the vertical position of a caption, and renders only the
band of the page holding the figure above it (default 330 pt) plus the
caption, at 110 dpi. One figure per image: this is the per-figure check, not
a contact sheet."""
import glob
import os
import re
import subprocess
import sys

PDF = sorted(glob.glob("build/one_quant_book_%02d_*.pdf" % int(os.environ.get("OQB_BOOK", "1"))))[0]
words = sys.argv[1].split()
out = sys.argv[2].removesuffix(".png")
height = float(sys.argv[3]) if len(sys.argv) > 3 else 330.0
npages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", PDF], capture_output=True, text=True).stdout).group(1))
for p in range(1, npages + 1):
    xml = subprocess.run(["pdftotext", "-bbox", "-f", str(p), "-l", str(p), PDF, "-"],
                         capture_output=True, text=True).stdout
    toks = re.findall(r'<word xMin="[\d.]+" yMin="([\d.]+)" xMax="[\d.]+" yMax="[\d.]+">([^<]*)</word>', xml)
    txt = [w for _, w in toks]
    for i in range(len(txt) - len(words) + 1):
        if txt[i:i + len(words)] == words:
            y = float(toks[i][0])
            dpi = 110
            s = dpi / 72.0
            top = max(0.0, y - height)
            subprocess.run(["pdftoppm", "-png", "-r", str(dpi), "-f", str(p), "-l", str(p),
                            "-x", "0", "-y", str(int(top * s)), "-W", str(int(595 * s)),
                            "-H", str(int((y - top + 45) * s)), "-singlefile", PDF, out], check=True)
            print(f"page {p}, caption at y={y:.0f}pt -> {out}.png")
            sys.exit(0)
print("caption not found:", " ".join(words), file=sys.stderr)
sys.exit(1)
