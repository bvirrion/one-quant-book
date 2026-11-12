# French pilot edition of One Quant Book 16 (`desk`)

Part of the Books 11–20 run, `sources/TRANSLATION_BOOKS_11-20_FR.md` (one coordinator, no subagents; session 2 closes
Books 16–20). Score file `translation_scores/book_16/fr/translation_score.md`.

| | |
|---|---|
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), 251 section calls, $2.14 list; coordinator `claude-opus-5-5` |
| Result | 88/100 (sampled), 373 pp, 0/0/0 under TeX Live 2026, `check_translation.sh` PASSED, linker `--check` 0 |
| Run directory | `draft/pilot-desk-fr/` (logs, sample, `sheet/` and `sheet2/`, `crops/`, `pdfsweep.txt`, `numrun.txt`, `fixes.py`, `figfix.py`) |

## Steps as run

1. `run.py --workers 3` in the step-4 queue (session 1): 0 files with a rejected section after pass 2.
2. `post.py --units`, `repair.py`, `post.py` (`draft/pilot-quant-fr/step5.sh`, all five books, three at once);
   `numrun2.py` (new) in the run directory: one invented row (solutions 15) removed, `\pounds` after a number made
   *livres*, before install.
3. `sites.py` (17 lines, all figure code read on the contact sheet), `install.py` (60 files); `FR_BOOKS` extended to 16;
   term links `--apply` (1,159).
4. `sweeps_all.sh desk`, then the three new sweeps (`currency_fr.py`, `unitlabel_fr.py`, `bare_def_lower.py`), now in
   `sweeps_all.sh` and run back over every French book.
5. Hand fixes: an English `\section{Exercises}` and weekend-problem title, an English half-line in solutions 23, typography
   in a TikZ node, eight tables and a header (`fixes.py`), 13 figures (`figfix.py`), Book 16's allow block in
   `tools/check_latin_prose.py`, and the twelve run-on captions of chs. 28–30 (English canon too).
6. Contact sheet of all 109 figures; crops of every repair; sample; three chapter openings; `pdfsweep.py`.

## Lessons

- **A sweep script's own blind spot hides a whole chapter range.** `sheet.py` took a caption only when *Figure* began
  within 120 pt of the left edge; chs. 28–30 printed their captions beside the picture, so the first sheet showed 97 of
  109 figures and nothing said so. Compare the sheet's count with the English figure count before reading it.
- **The model can invent a row.** Solutions 15 gained a *suivi de tendance* entry carrying the momentum row's numbers. It
  passed every structural check; only a number count per line (`numrun2.py`) saw a number with no English twin.
- **The English article rule needs a sweep per position.** `bare_def_fix.py` caught capitalised bare nouns; the
  lowercase ones that open a definition's first line escaped in eleven books (48). The new sweep takes the article from a
  gender table and reports any word it does not know.
- **Currency symbols other than `\$`** were never swept: `\euro` and `\pounds` before the amount survived in Books 1, 9
  and 17. Every currency macro needs the same rule.
