# French pilot edition of One Quant Book 14 (`networks`)

Part of the Books 11–20 run, `sources/TRANSLATION_BOOKS_11-20_FR.md` (one coordinator, no subagents; session 1 closes
Books 11–15). Score file `translation_scores/book_14/fr/translation_score.md`.

| | |
|---|---|
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), 304 section calls, $2.25 list; coordinator `claude-opus-5-5` |
| Result | 88/100 (sampled), 373 pp, 0/0/0 under TeX Live 2026, `check_translation.sh` PASSED, linker `--check` 0 |
| Run directory | `draft/pilot-networks-fr/` (logs, sample, `sheet/`, `crops/`, `pdfsweep.txt`, `figfr.py`, `fixes.py`) |

## Steps as run

1. `run.py --workers 3` in the step-4 queue: five passes (3, 3, 1, 1 files with a rejected section after passes 2–5). The
   last, ch. 3 §4 (one line flagged as English), was cleared before `post.py`: `rejected/` is empty and `post2.log` reports
   0 files with a rejected section.
2. `post.py --units`, `repair.py` (titles), `post.py`; `numrun.py` per line in the run directory; five lines fixed before
   install (chs. 3, 11, 13, 15, 16), and *feed handler* restored in chs. 3 and 20.
3. `sites.py` (43 lines), `install.py` (58 files); `FR_BOOKS` extended to 14; term links `--apply` (853).
4. `sweeps_all.sh networks`.
5. Hand fixes: the 43 `sites` lines (`figfr.py` holds the tick and `meta` label tables of 13 chapters), four bare definitions,
   13 overfull boxes (`fixes.py`), an allow block for Book 14 in `tools/check_latin_prose.py`, 13 figure collisions.
6. Contact sheet of all 97 figures; crops of every repair; sample; three chapter openings; `pdfsweep.py`.

## Lessons

- **A TikZ picture that draws from fixed coordinates next to a text node breaks when the French text is wider.** Fig. 9.1
  started its cables at `x = 0.95`, the English node's edge, so they crossed the French label. Anchor to the node
  (`(me.east |- 0,0.6)`), not to a number.
- **A rendering that is right in general can be wrong in the book's field.** *point d'échange* for a handoff reads as an
  internet exchange point in a networks book. Pin desk words with a field-specific meaning in the glossary as `00` lines.
- **Ordinals without `\up{e}`**: Haiku writes *99e centile* about one time in four. `\up{e}~centile` is the series form; the
  fix (ordinal before *centile*/*percentile*, outside math and `\texttt`, and right after `{` in legends) ran over every French
  book: 80 instances, Books 2, 3, 6–9, 11–14.
- **French solutions live in `parts/<slug>/solutions/fr/`, not under `parts/<slug>/fr/`.** A sweep over `*/fr/` misses them;
  glob both.
- A long y label taller than the plot prints above the frame. Shorten it to the plot's height (*rafraîchissement complet
  (ms)*), rather than enlarge the plot.
