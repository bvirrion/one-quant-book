# French pilot edition of One Quant Book 12 (`ml`)

Part of the Books 11–20 run, `sources/TRANSLATION_BOOKS_11-20_FR.md` (one coordinator, no subagents; session 1 closes
Books 11–15). Score file `translation_scores/book_12/fr/translation_score.md`.

| | |
|---|---|
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), 291 section calls, $2.47 list; coordinator `claude-opus-5-5` |
| Result | 88/100 (sampled), 370 pp, 0/0/0 under TeX Live 2026, `check_translation.sh` PASSED, linker `--check` 0 |
| Run directory | `draft/pilot-ml-fr/` (logs, sample, `sheet/`, `crops/`, `pdfsweep.txt`, `tabs.py`) |

## Steps as run

1. `run.py --workers 3` in the step-4 queue: 11 files with a rejected section after pass 1, 5, 3, 2, 2 after passes 2–5.
   Of the last two: ch. 22 flagged two pgfplots `table[...]` lines as English (accepted, `accept.py --english-ok`);
   ch. 26 reordered a figure (one `redo.py` call cleared it).
2. `post.py`, `repair.py` (5 lines), `post.py`. NUMDIFF found two losses (solutions 14 dropped a whole clause with three
   numbers; ch. 3 dropped a chapter reference) and seven lines of decimal commas; all fixed in the run directory.
3. `sites.py`, `install.py` (58 files); `FR_BOOKS` extended to 12; term links `--apply` (1,212).
4. Shared sweeps through the new `draft/pilot-quant-fr/sweeps_all.sh ml` (all fixers, then the reports).
5. Hand fixes: the five `sites` lines (Fig. 26.1's tick labels came from a CSV column in English, now written out in
   French), two bare definitions, the prose gate's blocking fragments, twelve tables (`work`: `draft/pilot-ml-fr/tabs.py`),
   two TikZ pictures, one `sloppypar`, nine figure collisions.
6. Contact sheet of all 62 figures; crops of the repaired ones; sample; three chapter openings; `pdfsweep.py`.

## Lessons

- **`numfile.py` reads `parts/`, so before install read NUMDIFF per line in the run directory**: `numrun.py <slug>
  course/NN solutions/NN` (new) prints each line whose numbers differ, with English and French side by side. It found
  both losses in minutes.
- The twin prose gate does not parse a local macro's arguments: Fig. 3.1's `\row{4}{shuffled $k$-fold}` passed every
  gate in English. Read the contact sheet for labels, not only for collisions.
- `yticklabels from table={…}{col}` prints a CSV column: English data in a French figure. Write the labels out in the
  French file (`yticklabels={…}`) rather than editing shared data.
- A section whose only flag is pgfplots code (`table[x=…,y=…]`, `restrict expr to domain`) is a false "left in English":
  accept it, don't burn redo calls.
- `bare_def_fix.py` now takes any verb after the optional English parenthesis, and definitions that open after a full
  stop; a skip list holds names (*Adam*) and verb phrases (*Prédire puis optimiser*).
