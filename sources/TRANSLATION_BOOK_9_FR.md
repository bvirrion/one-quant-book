# French pilot edition of One Quant Book 9 (`strategies-2`)

Part of the Books 6–10 run, `sources/TRANSLATION_BOOKS_6-10_FR.md` (one coordinator, no subagents). Score file
`translation_scores/book_9/fr/translation_score.md`.

| | |
|---|---|
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), 243 section calls, $1.68 list; coordinator `claude-opus-5-5` |
| Result | 88/100 (sampled), 356 pp, 0/0/0 under TeX Live 2026, `check_translation.sh` PASSED, linker `--check` 0 |
| Run directory | `draft/pilot-strategies-2-fr/` (`work/` holds this book's hand fixes and logs) |

## Steps as run

1. `run.py --workers 3` in the step-4 queue, 0 rejected.
2. `post.py`, `repair.py`, `post.py` again (one orphan line: a split `\texttt`).
3. `sites.py`, `install.py` (58 files); Fig. 4.1's rule labels mapped through `\pgfkeys`.
4. Term links and census (one missed link fixed by hand).
5. Shared sweeps in `draft/pilot-quant-fr/`: `fix_common.py` (one false hit restored, then the script fixed), `typo_apply.py`,
   `dollars_apply.py`, `crefart_apply.py` (no change), `iqroles_fr.py`, `texttt_join.py`, `wkend_labels.py`, `quotes_fr.py`,
   the reports.
6. Hand fixes: ch. 25 Part titles, 13 bare definitions, stranded articles, the prose gate's three fragments,
   `work/hand3.py` (18 tables with `tabspec.py`), three more by hand, six figure collisions.
7. Contact sheet of all 57 figures, `pdfsweep.py`, sample, `numfile.py`; final build into `build/` at the close of the run.

## Lessons carried to Book 10

- Check `\iqroles`, the weekend-problem labels and English quotes before the first build: all three come back from Haiku in
  every book.
- `numfile.py` (per-file multisets) replaces `numlines.py` once tables have been given `\tabcolsep` lines.
