#!/usr/bin/env python3
"""Renumber one chapter's questions after inserting new ones, by their order in the chapter file.

Put each new question in the chapter file where it belongs in star order, with any number not yet used
(say 901, 902, ...) in its label, and give its answer and test that same number. Then, from the repo root:

    .venv/bin/python sources/interviews-3/renumber.py 01-algorithms           # dry run: prints the mapping
    .venv/bin/python sources/interviews-3/renumber.py 01-algorithms --apply

It numbers the labels 1, 2, 3, ... in the order they appear in parts/interviews-3/<chapter>.tex, and rewrites, in
two phases so that numbers cannot collide:
- every iq:iv3:<slug>:N in the chapter file and in parts/interviews-3/solutions/<chapter>.tex;
- the order of the solution blocks, to match;
- def test_qN and the keys of NONNUMERIC in code/interviews-3/<chapter>/tests/test_solutions.py;
- Q<N> in the "used in" column of sources/interviews-3/<chapter>.md.

Listing labels, module names and file names carry no question numbers, so nothing else moves. Prose that says
"question 12" would not be caught: the rules forbid it. Run the chapter's tests and the gate afterwards.
"""
import argparse
import pathlib
import re
import sys


def renumber(root, chapter, apply):
    slug = chapter.split("-", 1)[1]
    label = re.compile(rf"iq:iv3:{re.escape(slug)}:(\d+)")
    paths = {
        "chapter": root / "parts/interviews-3" / f"{chapter}.tex",
        "answers": root / "parts/interviews-3/solutions" / f"{chapter}.tex",
        "tests": root / "code/interviews-3" / chapter / "tests/test_solutions.py",
        "ledger": root / "sources/interviews-3" / f"{chapter}.md",
    }
    text = {k: p.read_text(encoding="utf-8") for k, p in paths.items() if p.exists()}
    order = re.findall(rf"\\begin\{{question\}}\[[^\n]*?\]\\label\{{iq:iv3:{re.escape(slug)}:(\d+)\}}", text["chapter"])
    if len(order) != len(set(order)):
        sys.exit(f"duplicate numbers in the chapter file: {order}")
    mapping = {int(old): i for i, old in enumerate(order, 1)}
    moved = {o: n for o, n in mapping.items() if o != n}
    print(f"{chapter}: {len(order)} questions, {len(moved)} renumbered")
    for o, n in moved.items():
        print(f"  {o} -> {n}")
    answers = label.findall(text["answers"])
    missing = sorted({int(a) for a in answers} ^ set(mapping))
    if missing:
        sys.exit(f"questions and answers do not match: {missing}")
    if not apply:
        print("dry run: nothing written (use --apply)")
        return

    def relabel(t):
        return re.sub(label, lambda m: f"iq:iv3:{slug}:{mapping[int(m.group(1))]}", t)

    text["chapter"] = relabel(text["chapter"])
    block = r"\\begin\{solution\}\{iq:iv3:[^}]+:(\d+)\}.*?\\end\{solution\}\n*"
    blocks = list(re.finditer(block, text["answers"], flags=re.S))
    head = text["answers"][: blocks[0].start()]
    tail = text["answers"][blocks[-1].end() :]
    by_new = sorted(blocks, key=lambda m: mapping[int(m.group(1))])
    joined = "\n".join(m.group(0).rstrip("\n") + "\n" for m in by_new)
    text["answers"] = relabel(head + joined + tail)
    if "tests" in text:
        t = text["tests"]
        t = re.sub(r"\bdef test_q(\d+)\b", lambda m: f"def test_qTMP{mapping.get(int(m.group(1)), int(m.group(1)))}", t)
        t = t.replace("def test_qTMP", "def test_q")
        m = re.search(r"^NONNUMERIC = \{.*?^\}", t, flags=re.S | re.M)
        if m:
            def key(k):
                return f"{k.group(1)}{mapping.get(int(k.group(2)), int(k.group(2)))}:"

            body = re.sub(r"^(\s*)(\d+):", key, m.group(0), flags=re.M)
            t = t[: m.start()] + body + t[m.end() :]
        text["tests"] = t
    if "ledger" in text:
        out = []
        for line in text["ledger"].splitlines():
            if line.startswith("|") and "|" in line[1:]:
                cells = line.split("|")
                cells[-2] = re.sub(r"\bQ(\d+)\b", lambda q: f"Q{mapping[int(q.group(1))]}", cells[-2])
                line = "|".join(cells)
            out.append(line)
        text["ledger"] = "\n".join(out) + "\n"
    for k, t in text.items():
        paths[k].write_text(t, encoding="utf-8")
    print("written")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("chapter")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--root", default=".")
    a = ap.parse_args()
    renumber(pathlib.Path(a.root), a.chapter, a.apply)
