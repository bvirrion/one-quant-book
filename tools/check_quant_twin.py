#!/usr/bin/env python3
"""Gate 12 of check_translation.sh: the code a translated file prints must be its English twin's, ON DISK.

id_apply.py's `code` census checks this when a file is written, but a post-write edit (a sweep, a hand fix, the
term linker) is seen by nothing else. Compared per file, against the English twin found by path
(parts/<slug>/<lang>/NN.tex -> parts/<slug>/NN.tex):

  * the ordered \\omcode{path}{first}{last} triples: a listing is included from a tested file by those three
    arguments, so a changed digit prints the wrong lines and no build notices;
  * the ordered \\begin{dated}{YYYY-MM} dates: the box title is built from them;
  * the ordered \\texttt{} contents: identifiers from the tested code, never prose;
  * the ordered math spans (id_apply.math_spans, \\text{} blanked), whitespace collapsed and two moves the series
    card allows taken out: a currency sign `\\$` leaving the span (`$… = \\$60$` -> `$… = 60$~\\$`) and a space
    before `\\%`. A typography sweep run after install put `~:` inside `$…$` (quant Book 4 fr, 2026-11-10) and
    nothing saw it.

Usage:
    python3 tools/check_quant_twin.py [--quiet] parts/markets-1/fr parts/markets-1/solutions/fr
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import id_apply as A  # noqa: E402
import re  # noqa: E402


def math_norm(text: str):
    out = []
    for m in A.math_spans(text):
        m = m.replace("\\$", "")
        m = re.sub(r"(?:~|\\,|\\ )\\%", r"\\%", m)
        out.append(" ".join(m.split()))
    return out


def twin(path: pathlib.Path) -> pathlib.Path:
    return path.parent.parent / path.name


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    files = bad = 0
    for d in map(pathlib.Path, args.dirs):
        if not d.is_dir():
            print("  quant twin: not a directory: %s" % d)
            return 1
        for f in sorted(d.glob("[0-9][0-9]-*.tex")):
            e = twin(f)
            if not e.is_file():
                continue
            files += 1
            et = A.unwrap_omterm(e.read_text(encoding="utf-8"))
            ft = A.unwrap_omterm(f.read_text(encoding="utf-8"))
            a = A.code_args(et) + [("math", x) for x in math_norm(et)]
            b = A.code_args(ft) + [("math", x) for x in math_norm(ft)]
            if a != b:
                bad += 1
                dd = A.first_diff(a, b)
                print("  %s: code or math differs from English at #%d: EN %r / %s %r"
                      % (f, dd[0], dd[1], f.parent.name.upper(), dd[2]))
    if files == 0:  # a gate that saw nothing has not passed
        print("  quant twin: NO FILES FOUND under %s" % " ".join(args.dirs))
        return 1
    if not args.quiet or bad:
        print("  quant twin: %d file(s), %d differ" % (files, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
