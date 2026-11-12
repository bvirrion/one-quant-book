# French pilot edition of One Quant Book 15 (`platforms`)

Part of the Books 11–20 run, `sources/TRANSLATION_BOOKS_11-20_FR.md` (one coordinator, no subagents; session 1 closes
Books 11–15). Score file `translation_scores/book_15/fr/translation_score.md`.

| | |
|---|---|
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), 314 section calls, $2.38 list; coordinator `claude-opus-5-5` |
| Result | 88/100 (sampled), 395 pp, 0/0/0 under TeX Live 2026, `check_translation.sh` PASSED, linker `--check` 0 |
| Run directory | `draft/pilot-platforms-fr/` (logs, sample, `sheet/`, `crops0/` before, `crops/` after, `pdfsweep.txt`, `figfr.py`, `fixes.py`, `figfix.py`) |

## Steps as run

1. `run.py --workers 3` in the step-4 queue: five passes (9, 4, 4, 3, 2 files with a rejected section after passes
   1–5). The last two were cleared with `accept.py --english-ok` (a line of code identifiers each) before `post.py`;
   `post2.log` reports 0 files with a rejected section.
2. `post.py --units`, `repair.py` (titles), `post.py`; `numrun.py` per line in the run directory. Fixed before install:
   a stray `=` line (ch. 25), `1.5~Go` (ch. 8), two percentages (ch. 22), *pages* → *alertes* (ch. 28 and its
   solutions).
3. `sites.py` (90 lines), `install.py` (60 files); `FR_BOOKS` extended to 15; term links `--apply` (922).
4. `sweeps_all.sh platforms`.
5. Hand fixes: the `sites` lines (`figfr.py`, 33 substitutions), twelve tables and four hyphenations (`fixes.py`), an
   allow block for Book 15 in `tools/check_latin_prose.py`, units (*Mo*, *Go/s*), clock times, 38 figure repairs
   (`figfix.py`, in ten passes, each followed by a rebuild and crops).
6. Contact sheet of all 110 figures; crops of every repair; sample; three chapter openings; `pdfsweep.py`.

## Lessons

- **A diagram laid out for English text overflows in French nearly everywhere.** 38 of 110 figures needed a repair, the
  most of any book so far. Most are three moves: break a node onto two or three lines (`\\` with `align=center`), spread
  the nodes by 0.2–0.5 cm, and cut a y label to the plot's height. Read every figure on the contact sheet, then crop
  each repair from the rebuilt PDF: about one repair in five needed a second pass.
- **A pgfplots legend in three columns overlaps its own entries** when the French text is long, and swapping `every
  even column` for `every odd column` only moves the gap. One column, inside the plot (with `ymax` raised to clear the
  bar labels), or below it, works.
- **The first word of a `p{}` cell never hyphenates**, so a long first word in a narrow header (*bibliothèque*) is an
  overfull box. Write `biblio\-thèque`.
- **Missing elision across a line break.** Haiku keeps the English line breaks, and an article that ends a line before a
  vowel stays unelided: *le agrégateur*, *la action*, *Le expected shortfall*. New `elision_fr.py` moves the break
  before the article and elides it, keeping the line count: 37 instances over twelve French books. Three were
  something worse, a dropped word (*la* ‹spirale› *a besoin*; *le* ‹changement›), found because the script leaves
  them for a hand check.
- **Second-person imperatives in exercises.** The series writes exercise items in the infinitive (*Énoncer le résultat
  nommé*) and interview questions in the imperative. New `imperative_fr.py` changes the head of an exercise item only,
  and skips lines that say *vous*: 36 instances over eight books. `iq_imperative.py` still reports 0 lines to change
  everywhere afterwards.
- **Wrong sense in a technical field**: Rust *crates* as *caisses*. Pin language-ecosystem words as `00` lines in the
  glossary.
- **A word with two meanings in one chapter**: the consumer's *offset* rendered *position* in a chapter about the
  *service de positions*. Write *position du consommateur* in full wherever positions are near.
