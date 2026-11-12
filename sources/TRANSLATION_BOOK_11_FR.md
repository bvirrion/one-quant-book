# French pilot edition of One Quant Book 11 (`hft`)

Part of the Books 11–20 run, `sources/TRANSLATION_BOOKS_11-20_FR.md` (one coordinator, no subagents; session 1 closes
Books 11–15). Score file `translation_scores/book_11/fr/translation_score.md`.

| | |
|---|---|
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), 239 section calls, $1.90 list; coordinator `claude-opus-5-5` |
| Result | 88/100 (sampled), 353 pp, 0/0/0 under TeX Live 2026, `check_translation.sh` PASSED, linker `--check` 0 |
| Run directory | `draft/pilot-hft-fr/` (logs, sample, contact sheet `sheet/`, crops `crops/`, `pdfsweep.txt`) |

## Steps as run

1. `run.py --workers 3` in the step-4 queue: 7 files with a rejected section after pass 1, 1 after pass 2, 0 after
   pass 3.
2. `post.py --units`, `repair.py`, `post.py` again. NUMDIFF: every difference read (euro placement, number words,
   12-hour clock to 24-hour, *4Q* → *T4*, line shifts). Chapter 20 came back with decimal commas: a real defect, fixed.
3. `sites.py`, `install.py` (58 files); `FR_BOOKS` in `tools/termlink/books.py` extended to 11.
4. Term links (430) and census.
5. Shared sweeps in `draft/pilot-quant-fr/`: `fix_common.py` (with new Book 11 agreement rules for *fiche*),
   `typo_apply.py`, `dollars_apply.py`, `crefart_apply.py`, `iqroles_fr.py`, `texttt_join.py`, `wkend_labels.py`,
   `quotes_fr.py`, `index_join.py`, the new `bare_def_fix.py` (definitions opening on a bare capitalised noun), the
   reports.
6. Hand fixes: chapter 20's weekend-problem Part labels, accent escapes, the prose gate's 11 figure fragments, two bare
   definitions, eleven tables (`tabspec.fix(..., tight=True)`), three `sloppypar`, one legend.
7. Contact sheet of all 68 figures; nine figures repaired and re-read in crops (two needed a second fix).
8. Sample (seed 1) read: four fixes, and the new `iq_imperative.py` (13 interview questions from the infinitive to the
   imperative).

## Lessons

- Interview questions address the candidate: imperative (*Dérivez*, *Expliquez*). Haiku follows the exercises'
  infinitive about one time in five. `iq_imperative.py <slug> [--apply]` fixes the openers and the verbs coordinated
  with them, and lists infinitive openers it doesn't know (*Racheter, couvrir ou conserver~?* is a real infinitive
  question and stays).
- A y-label longer than the plot is tall gets clipped at the page side (Figs. 14.1, 22.2). Shorten it when the caption
  already carries the full name.
- Long French legends inside a plot cover the data. Put them above the axis (`at={(0.5,1.03)},anchor=south`).
