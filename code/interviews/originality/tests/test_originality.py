"""Originality gate for Book 18: no 8-word run of a Book 18 question or solution appears in Books 1-17.

Every interviewq, exercise, problem, solution and example environment of every other book is compared with every
Book 18 question and solution, after normalisation (TeX commands and labels stripped, lower case, numbers
kept). The test prints how many texts it compared and fails if it compared none.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[4]
PARTS = ROOT / "parts"
N = 8
ENV = re.compile(r"\\begin\{(interviewq|exercise|problem|solution|example)\}(.*?)\\end\{\1\}", re.S)
DROP = re.compile(
    r"\\(?:label|ref|cref|Cref|eqref|pageref|index|iqroles|iqfirm|omcode|includegraphics)\*?"
    r"(?:\[[^\]]*\])?\{[^{}]*\}(?:\{[^{}]*\})*"
)
TOKEN = re.compile(r"[a-z]+|\d+(?:\.\d+)?")
# Boilerplate every solution may share: the look-for opening and the book-pointer phrases.
EXEMPT = [
    "what the interviewer is looking for",
    "one quant book",
]


def tokens(tex: str) -> list[str]:
    tex = re.sub(r"(?<!\\)%.*", " ", tex)
    tex = re.sub(r"^\{[^{}]*\}|^\[[^\]]*\]", " ", tex.lstrip())  # the environment's own argument
    tex = DROP.sub(" ", tex)
    tex = re.sub(r"\\[a-zA-Z]+\*?", " ", tex)
    return TOKEN.findall(tex.lower())


def shingles(toks: list[str]) -> set[tuple[str, ...]]:
    out = set()
    for i in range(len(toks) - N + 1):
        sh = tuple(toks[i : i + N])
        words = [w for w in sh if w.isalpha() and len(w) > 2]
        if len(words) < 5:  # formula-only or number-only runs are not wording
            continue
        text = " ".join(sh)
        if any(e in text for e in EXEMPT):
            continue
        out.add(sh)
    return out


def texts(book_dir: pathlib.Path):
    for f in sorted(book_dir.rglob("*.tex")):
        for m in ENV.finditer(f.read_text(encoding="utf-8")):
            yield f, m.group(2)


def test_no_shared_eight_word_run():
    ours = {}
    for f, body in texts(PARTS / "interviews"):
        for sh in shingles(tokens(body)):
            ours.setdefault(sh, f.relative_to(ROOT))
    compared, hits = 0, []
    for book in sorted(p for p in PARTS.iterdir() if p.is_dir() and p.name != "interviews"):
        for f, body in texts(book):
            compared += 1
            for sh in shingles(tokens(body)) & ours.keys():
                hits.append((str(ours[sh]), str(f.relative_to(ROOT)), " ".join(sh)))
    n_ours = sum(1 for _ in texts(PARTS / "interviews"))
    print(f"originality: {n_ours} Book 18 texts ({len(ours)} shingles) against {compared} texts of Books 1-17")
    assert n_ours > 300 and compared > 1000, "the gate saw too few texts to have passed"
    assert not hits, "\n".join(" | ".join(h) for h in hits[:40]) + f"\n{len(hits)} shared runs"
