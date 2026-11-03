"""Originality gate for one interview book: our wording is our own.

Compares every question and answer of this book with (a) every interviewq, exercise, problem, solution
and example of Books 1-17, and (b) the question and evidence fields of the interview harvest. A shared run of eight
words fails. The previous Book 18 and the other interview books are not compared here: `tools/check_interview_book.py --cross`
compares the three books with each other.

A shared idea is fine, because classic problems are welcome. Shared wording is what this catches. Short harvest titles
have no eight-word run, so near-copies of those are printed for a human to read, without failing.
"""
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve()
REPO = HERE.parents[4]
OURS = REPO / "parts" / HERE.parents[2].name
HARVEST = REPO / "sources" / "interview-harvest"
N = 8
OUR_ENV = re.compile(r"\\begin\{(question|solution)\}(.*?)\\end\{\1\}", re.S)
ENV = re.compile(r"\\begin\{(interviewq|exercise|problem|solution|example)\}(.*?)\\end\{\1\}", re.S)
DROP = re.compile(
    r"\\(?:label|ref|cref|Cref|eqref|pageref|index|iqroles|iqfirm|iqlevel|omcode|includegraphics)\*?"
    r"(?:\[[^\]]*\])?\{[^{}]*\}(?:\{[^{}]*\})*"
)
TOKEN = re.compile(r"[a-z]+|\d+(?:\.\d+)?")
EXEMPT = ["one quant book", "why it matters", "classic wrong answer"]


def tokens(tex: str) -> list[str]:
    tex = re.sub(r"(?<!\\)%.*", " ", tex)
    tex = re.sub(r"^\{[^{}]*\}|^\[[^\]]*\]", " ", tex.lstrip())
    tex = DROP.sub(" ", tex)
    tex = re.sub(r"\\[a-zA-Z]+\*?", " ", tex)
    return TOKEN.findall(tex.lower())


def shingles(toks: list[str]) -> set[tuple[str, ...]]:
    out = set()
    for i in range(len(toks) - N + 1):
        sh = tuple(toks[i : i + N])
        if sum(w.isalpha() and len(w) > 2 for w in sh) < 5:  # formula-only or number-only runs are not wording
            continue
        if not any(e in " ".join(sh) for e in EXEMPT):
            out.add(sh)
    return out


def our_texts():
    for f in sorted(OURS.rglob("*.tex")):
        if f.name == "tracks.tex":
            continue
        for m in OUR_ENV.finditer(f.read_text(encoding="utf-8")):
            yield f.relative_to(REPO), m.group(2)


def book_texts():
    for book in sorted(p for p in (REPO / "parts").iterdir() if p.is_dir() and not p.name.startswith("interviews")):
        for f in sorted(book.rglob("*.tex")):
            for m in ENV.finditer(f.read_text(encoding="utf-8")):
                yield f"{f.relative_to(REPO)}", m.group(2)


def harvest_rows():
    for path in sorted(HARVEST.glob("*.jsonl")):
        if path.stem not in {"mm", "crypto", "bank", "hf"}:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                yield json.loads(line)


def test_no_shared_eight_word_run():
    ours, n_ours, our_joined = {}, 0, []
    for where, body in our_texts():
        n_ours += 1
        toks = tokens(body)
        our_joined.append((where, " ".join(toks)))
        for sh in shingles(toks):
            ours.setdefault(sh, where)
    hits, n_books, n_rows = [], 0, 0
    for where, body in book_texts():
        n_books += 1
        for sh in shingles(tokens(body)) & ours.keys():
            hits.append((str(ours[sh]), where, " ".join(sh)))
    near = []
    for row in harvest_rows():
        n_rows += 1
        for field in ("question", "evidence"):
            toks = TOKEN.findall(row[field].lower())
            for sh in shingles(toks) & ours.keys():
                hits.append((str(ours[sh]), f"harvest {row['source_site']}", " ".join(sh)))
            if field == "question" and 5 <= len(toks) < N:
                title = " ".join(toks)
                near += [f"{where}: {title}" for where, text in our_joined if title in text]
    print(f"originality: {n_ours} texts, {len(ours)} shingles, against {n_books} book texts and {n_rows} harvest rows")
    for item in sorted(set(near))[:40]:
        print("  near a short harvest title (read it):", item)
    assert n_books > 1000, "the gate saw too few book texts to have passed"
    # The harvest is optional: CI may run without it.
    assert n_rows > 1000 or not HARVEST.exists(), "the gate saw too few harvest rows to have passed"
    assert n_ours > 0, "no questions found"
    assert not hits, "\n".join(" | ".join(h) for h in hits[:40]) + f"\n{len(hits)} shared runs"
