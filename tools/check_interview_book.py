#!/usr/bin/env python3
"""The gate for the interview books (sources/INTERVIEW_BOOKS.md). Exit 1 on any failure.

Usage:
  .venv/bin/python tools/check_interview_book.py interviews-1          while writing: lists chapters not yet written
  .venv/bin/python tools/check_interview_book.py interviews-1 --final  closing: every outline chapter, exact counts
  .venv/bin/python tools/check_interview_book.py --cross               no shared stem wording across the three books

Checks every chapter listed in parts/<slug>/part.tex against its answers, tests and ledger, then the book-wide rules,
then the build log. Prints each chapter's answer word counts, so depth is visible as well as structure.
"""
import hashlib
import pathlib
import re
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BOOKS = {
    "interviews-1": ("iv1", "one_quant_book_18_interviews_1"),
    "interviews-2": ("iv2", "one_quant_book_19_interviews_2"),
    "interviews-3": ("iv3", "one_quant_book_20_interviews_3"),
}
BOOK = ""
PREFIX = ""
PARTS = ROOT
FINAL = False
TEST_CHAPTERS = ("timed-test", "speed-drills")
CODE_MEDIAN_FLOOR = 170
MAX_LISTING_LINE = 94
ROLES = {"QR", "QT", "Trader", "Analyst", "DS", "QD", "Dev", "LLE", "Risk"}
FIRMS = {"market maker", "crypto", "bank", "hedge fund", "any"}
LEVELS = {"junior", "experienced"}
BANNED_ENVS = ("definition", "theorem", "proposition", "lemma", "method", "example", "exercise", "problem",
               "interviewq", "lstlisting", "strategyfile", "tutorial", "build")
BANNED_STEM = re.compile(
    r"\b(this|the|previous|next|earlier|last) (chapter|section)\b|\b(previous|next|last|earlier|preceding) question\b"
    r"|\bas above\b|\bsee question\b|\\ref\{", re.I)
# Words that must never print, kept as one-way hashes so that this file doesn't spell them out.
ALWAYS_BANNED_HASHES = {
    "cf12f8f5bc9976971df6a9a5a3eec4289aab466636cb7f7fc8dce1626b3660f6",
    "c574a172dfa4eef63c8ad3a297807e6e9c7d1556f37daca3b5807b938044533d",
    "b39f4d657623ab79ce38f7b5c5c16b749fe9d65c64c7500290f8d4b5653d5f39",
    "a8cbec35401b68f84e07fb7a1748be3028fa2914653831e26e08e0202d905cd8",
    "8ee9938e4b960a50540f1ca9299facc5a5f342d0848b402c322fd14592e4bc32",
    "427c508339ac90f63ee04e94059593ba9a35ae4ee7c099dbb3c15e6cd79736c0",
}


def banned_words(text):
    """Return the words of text whose lower-case form hashes to a banned word."""
    words_seen = set(re.findall(r"[A-Za-z]+", text))
    return sorted(w for w in words_seen if hashlib.sha256(w.lower().encode()).hexdigest() in ALWAYS_BANNED_HASHES)


Q = re.compile(
    r"\\begin\{question\}(\[(?:[^\[\]]|\[[^\]]*\])*\])?\s*\\label\{(iq:iv\d:[^}]+)\}(.*?)\\end\{question\}", re.S
)
A = re.compile(r"\\begin\{solution\}\{([^}]+)\}(.*?)\\end\{solution\}", re.S)

fails = []


def bad(where, what):
    fails.append(f"{where}: {what}")


def words(tex):
    tex = re.sub(r"(?<!\\)%.*", " ", tex)
    tex = re.sub(r"\\(?:index|label|omcode|cref|Cref|ref|pageref)\*?(?:\{[^{}]*\})+", " ", tex)
    tex = re.sub(r"\\\[.*?\\\]|\$[^$]*\$", " x ", tex, flags=re.S)
    tex = re.sub(r"\\[a-zA-Z]+\*?", " ", tex)
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]*", tex))


def tags(opt):
    out = {}
    out["stars"] = opt.count(r"\star")
    for name in ("iqroles", "iqfirm", "iqlevel"):
        m = re.search(r"\\" + name + r"\{([^}]*)\}", opt)
        out[name] = [x.strip() for x in m.group(1).split(",")] if m else None
    return out


def outline():
    rows, here = {}, False
    for line in (ROOT / "outline" / "interviews.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            here = line[3:].split()[0] == BOOK
        m = re.match(r"\|\s*(\d+)\s*\|\s*([a-z0-9-]+)\s*\|\s*(\d+)\s*\|", line)
        if here and m:
            rows[f"{int(m.group(1)):02d}-{m.group(2)}"] = int(m.group(3))
    return rows


def check_listings(stem, tex):
    for path, first, last in re.findall(r"\\omcode\{([^}]+)\}\{(\d+)\}\{(\d+)\}", tex):
        try:
            lines = (ROOT / path).read_text(encoding="utf-8").splitlines()[int(first) - 1 : int(last)]
        except OSError:
            continue  # tools/check_omcode.py reports a missing file
        for i, line in enumerate(lines, int(first)):
            if len(line) > MAX_LISTING_LINE:
                bad(stem, f"{path}:{i} is {len(line)} characters (a printed line is at most {MAX_LISTING_LINE})")


def check_prose_code(stem, tex):
    for m in re.finditer(r"\\texttt\{([^{}]*)\}", tex):
        if ">>" in m.group(1) or "<<" in m.group(1) or "'" in m.group(1):
            bad(stem, f"\\texttt with >>, << or a straight apostrophe prints wrongly: {m.group(0)[:50]}")


def check_log():
    log = ROOT / "build" / f"{BOOKS[BOOK][1]}.log"
    if not log.exists():
        bad(BOOK, f"no build log {log.name}: build the book first")
        return
    text = log.read_text(encoding="latin-1")
    e = len(re.findall(r"^!", text, re.M))
    u = len(re.findall(r"undefined", text, re.I))
    o = text.count("Overfull")
    print(f"log: errors {e} / undefined {u} / overfull {o}")
    if (e, u, o) != (0, 0, 0):
        bad(BOOK, f"build log has {e} errors, {u} undefined, {o} overfull")


def forbidden_names():
    names = []
    for line in (ROOT / "tools" / "firm_names.txt").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            names.append(line.strip())
    return names


def check_chapter(stem, expected, firm_names):
    ch, sol = PARTS / f"{stem}.tex", PARTS / "solutions" / f"{stem}.tex"
    slug = stem.split("-", 1)[1]
    is_test = slug.startswith(TEST_CHAPTERS)
    if expected == 0:  # a chapter of text with no questions, such as how to train
        if not ch.exists():
            bad(stem, "missing chapter file")
            return None
        body = ch.read_text(encoding="utf-8")
        if f"\\label{{ch:{PREFIX}:{slug}}}" not in body:
            bad(stem, "chapter label missing")
        if '"' in re.sub(r"(?<!\\)%.*", "", body):
            bad(stem, "straight quote")
        ledger = ROOT / "sources" / BOOK / f"{stem}.md"
        ledger_text = ledger.read_text(encoding="utf-8") if ledger.exists() else ""
        if not ledger.exists():
            bad(stem, "no ledger file")
        for name in banned_words(body):
            bad(stem, f"banned name {name}")
        for name in firm_names:
            if re.search(r"\b" + re.escape(name) + r"\b", body) and name not in ledger_text:
                bad(stem, f"firm name {name} without a ledger row")
        print(f"{stem:<44} text chapter, {words(body)} words")
        return []
    if not ch.exists() or not sol.exists():
        bad(stem, "missing chapter or solutions file")
        return None
    body, answers = ch.read_text(encoding="utf-8"), sol.read_text(encoding="utf-8")

    if f"\\label{{ch:{PREFIX}:{slug}}}" not in body:
        bad(stem, "chapter label missing")
    if not is_test and "\\begin{ivtrains}" not in body:
        bad(stem, "no ivtrains block")
    for env in BANNED_ENVS:
        if f"\\begin{{{env}}}" in body or f"\\begin{{{env}}}" in answers:
            bad(stem, f"environment {env} is not used in this book")
    if not answers.lstrip().startswith(f"\\section*{{Chapter \\ref{{ch:{PREFIX}:{slug}}}"):
        bad(stem, "solutions file does not open with the chapter heading")

    questions = list(Q.finditer(body))
    labels = [m.group(2) for m in questions]
    if body.count("\\begin{question}") != len(questions):
        bad(stem, "a question has no label directly after its options")
    if expected is not None and len(questions) != expected:
        if FINAL or len(questions) > expected:
            bad(stem, f"{len(questions)} questions, the outline says {expected}")
        else:
            print(f"  TODO {stem}: {len(questions)} of {expected} questions so far")
    want = [f"iq:{PREFIX}:{slug}:{i}" for i in range(1, len(labels) + 1)]
    if labels != want:
        bad(stem, f"labels are not 1..n in order: {[a for a, b in zip(labels, want, strict=True) if a != b][:4]}")

    last_stars = 0
    for m in questions:
        label, stem_text = m.group(2), m.group(3)
        opt = m.group(1) or ""
        t = tags(opt)
        if is_test:
            if any(t[k] for k in ("iqroles", "iqfirm", "iqlevel")) or t["stars"]:
                bad(label, "a timed test or drill sheet carries no stars or tags")
        else:
            if not 1 <= t["stars"] <= 4:
                bad(label, f"{t['stars']} stars")
            if t["stars"] < last_stars:
                bad(label, "stars go down: order by non-decreasing stars")
            last_stars = t["stars"]
            if "any" in (t["iqfirm"] or []) and len(t["iqfirm"]) > 1:
                bad(label, "firm tag 'any' stands alone")
            for key, vocab in (("iqroles", ROLES), ("iqfirm", FIRMS), ("iqlevel", LEVELS)):
                if not t[key]:
                    bad(label, f"no \\{key}")
                elif set(t[key]) - vocab:
                    bad(label, f"\\{key} has {sorted(set(t[key]) - vocab)}")
        if BANNED_STEM.search(stem_text):
            bad(label, f"refers to other text: {BANNED_STEM.search(stem_text).group(0)!r}")
        for cref in re.findall(r"\\[cC]ref\{([^}]*)\}", stem_text):
            if not cref.startswith("lst:"):
                bad(label, f"a stem may only \\cref a listing, not {cref}")
        if words(stem_text) < 8:
            bad(label, "stem under 8 words: is it complete?")

    found = list(A.finditer(answers))
    answer_labels = [m.group(1) for m in found]
    if answer_labels != labels:
        bad(stem, "answers do not match the questions, in order")
    by_stars = {}
    counts = []
    star_of = {m.group(2): tags(m.group(1) or "")["stars"] for m in questions}
    for m in found:
        n = words(m.group(2))
        counts.append(n)
        stars = star_of.get(m.group(1), 0)
        by_stars.setdefault(stars, []).append(n)
        if "\\iqlookfor" in m.group(2):
            bad(m.group(1), "\\iqlookfor is not used here")
        if stars == 1 and n < 25:
            bad(m.group(1), f"answer has {n} words (a one-star minimum is 25)")
        if stars >= 3 and n < 100:
            bad(m.group(1), f"answer has {n} words (three stars and up need 100)")
        if stars == 0 and n < 60:
            bad(m.group(1), f"timed-test answer has {n} words (minimum 60)")
        if re.search(r"\\emph\{[^}]*\}\s*\\index\{", m.group(2)):
            bad(m.group(1), "\\emph + \\index marks a definition: use a plain \\index")

    both = body + answers
    if '"' in re.sub(r"(?<!\\)%.*", "", both):
        bad(stem, "straight quote")
    if both.count("``") != both.count("''"):
        bad(stem, f"quote balance {both.count('``')} open, {both.count(chr(39) * 2)} close")
    for line in both.splitlines():
        if "..." in line and "\\dots" not in line and "\\foreach" not in line:
            bad(stem, f"drafty dots: {line.strip()[:60]}")
    if re.search(r"end\{[a-z]*>", both):
        bad(stem, "\\end{...> typo")
    if "\\omterm" in both:
        bad(stem, "\\omterm: this book has no term links")
    if re.search(r"\\(?:new|renew|provide)command|\\usepackage", both):
        bad(stem, "chapter files define no macros")

    check_listings(stem, both)
    check_prose_code(stem, both)

    test = ROOT / "code" / BOOK / stem / "tests" / "test_solutions.py"
    if not test.exists():
        bad(stem, f"no {test.relative_to(ROOT)}")
    else:
        src = test.read_text(encoding="utf-8")
        tested = {int(x) for x in re.findall(r"def test_q(\d+)\b", src)}
        m = re.search(r"NONNUMERIC\s*=\s*\{(.*?)\n?\}", src, re.S)
        exempt = {int(x) for x in re.findall(r"(\d+)\s*:", m.group(1))} if m else set()
        for i in range(1, len(labels) + 1):
            if i not in tested | exempt:
                bad(f"iq:{PREFIX}:{slug}:{i}", "neither a test_q nor in NONNUMERIC")
        if tested & exempt:
            bad(stem, f"both tested and NONNUMERIC: {sorted(tested & exempt)}")
    ledger = ROOT / "sources" / BOOK / f"{stem}.md"
    ledger_text = ledger.read_text(encoding="utf-8") if ledger.exists() else ""
    if not ledger.exists():
        bad(stem, "no ledger file")
    for name in banned_words(both):
        bad(stem, f"banned name {name}")
    for name in firm_names:
        if re.search(r"\b" + re.escape(name) + r"\b", both) and name not in ledger_text:
            bad(stem, f"firm name {name} without a ledger row")

    dist = "/".join(str(len(by_stars.get(s, []))) for s in (1, 2, 3, 4))
    med = statistics.median(counts) if counts else 0
    if BOOK == "interviews-3" and len(counts) >= 15 and med < CODE_MEDIAN_FLOOR:
        bad(stem, f"median answer {med:.0f} words (a code chapter aims at about 220, floor {CODE_MEDIAN_FLOOR})")
    figures = body.count("begin{omfigure}") + answers.count("begin{omfigure}")
    print(f"{stem:<44} q {len(questions):>3}  stars {dist:<11} answer words: median {med:>5.0f}, "
          f"min {min(counts, default=0):>3}, max {max(counts, default=0):>4}  figures {figures}")
    return counts


def cross():
    """No two of the three books share eight words running in a question stem."""
    seen, hits, total = {}, [], 0
    for book in BOOKS:
        for f in sorted((ROOT / "parts" / book).glob("[0-9]*.tex")):
            for m in Q.finditer(f.read_text(encoding="utf-8")):
                total += 1
                toks = re.findall(r"[a-z]+|\d+", re.sub(r"\\[a-zA-Z]+", " ", m.group(3)).lower())
                for i in range(len(toks) - 7):
                    sh = tuple(toks[i : i + 8])
                    if sum(w.isalpha() and len(w) > 2 for w in sh) < 5:
                        continue
                    where = seen.setdefault(sh, (book, m.group(2)))
                    if where[0] != book:
                        hits.append(f"{where[1]} and {m.group(2)}: {' '.join(sh)}")
    print(f"cross-book: {total} stems")
    for hit in hits[:40]:
        print("  SHARED", hit)
    print(f"CROSS-BOOK: {'GREEN' if not hits else f'RED ({len(hits)})'}")
    sys.exit(1 if hits else 0)


def main():
    global BOOK, PREFIX, PARTS, FINAL
    if "--cross" in sys.argv:
        cross()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1 or args[0] not in BOOKS:
        sys.exit(__doc__)
    BOOK, PREFIX, FINAL = args[0], BOOKS[args[0]][0], "--final" in sys.argv
    PARTS = ROOT / "parts" / BOOK
    part = (PARTS / "part.tex").read_text(encoding="utf-8")
    stems = re.findall(r"\\ominput\{[^}]+\}\{([^}]+)\}", part)
    sol_index = (PARTS / "solutions" / "solutions.tex").read_text(encoding="utf-8")
    sols = re.findall(r"\\ominputsol\{[^}]+\}\{([^}]+)\}", sol_index)
    plan = outline()
    if [s for s in stems if plan.get(s) != 0] != sols:
        bad("part.tex", "chapter list differs from solutions.tex")
    firm_names = forbidden_names()
    all_counts = []
    for stem in stems:
        if stem not in plan:
            bad(stem, "not in outline/interviews.md")
        counts = check_chapter(stem, plan.get(stem), firm_names)
        all_counts += counts or []
    missing = [s for s in plan if s not in stems]
    if missing:
        print(f"not written yet: {len(missing)} chapters")
        if FINAL:
            bad(BOOK, f"chapters missing: {missing[:6]}")
    if stems != sorted(stems):
        bad("part.tex", "chapters are not in the outline's number order")
    labels = re.findall(r"\\label\{([^}]*)\}", "".join(
        p.read_text(encoding="utf-8") for p in PARTS.rglob("*.tex") if p.name != "tracks.tex"
        # the English book only: a language edition (parts/<book>/fr/, solutions/fr/, generated/fr/) repeats its labels
        and not any(re.fullmatch(r"[a-z]{2}", d) for d in p.relative_to(PARTS).parts[:-1])))
    dups = {x for x in labels if labels.count(x) > 1}
    if dups:
        bad("book", f"duplicate labels {sorted(dups)[:5]}")
    if all_counts:
        print(f"book: {len(all_counts)} answers, median {statistics.median(all_counts):.0f} words")
        if len(all_counts) >= 20 and statistics.median(all_counts) < 120:
            bad("book", f"median answer {statistics.median(all_counts):.0f} words (target about 140, floor 120)")
    if not stems:
        bad("book", "no chapters listed")
    check_log()
    for line in fails:
        print("  FAIL", line)
    print("INTERVIEW GATE: " + ("GREEN" if not fails else f"RED ({len(fails)})"))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
