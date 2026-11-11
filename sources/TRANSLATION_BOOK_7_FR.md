# French pilot edition of One Quant Book 7 (`research`)

Part of the Books 6–10 run, `sources/TRANSLATION_BOOKS_6-10_FR.md` (one coordinator, no subagents). Score file
`translation_scores/book_7/fr/translation_score.md`.

| | |
|---|---|
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), 280 section calls, $2.39 list; coordinator `claude-opus-5-5` |
| Result | 88/100 (sampled), 370 pp, 0/0/0 under TeX Live 2026, `check_translation.sh` PASSED, linker `--check` 0 |
| Run directory | `draft/pilot-research-fr/` (`work/` holds this book's hand fixes and logs) |

## Steps as run

1. `run.py --workers 3` in the step-4 queue: 4 passes, 0 rejected.
2. `post.py`, `repair.py` (15 sites), `post.py` again; NUMDIFF on 12 files, all explained at line level.
3. `sites.py` (9 lines), `install.py`; French tick labels in ch. 3, 25 and 26.
4. Term links and census (two missed links fixed by hand).
5. Shared sweeps in `draft/pilot-quant-fr/`: `fix_common.py`, `typo_apply.py`, `dollars_apply.py`, `crefart_apply.py` (no
   change), `sweep_report.py`, `shift_report.py`, `extra_report.py`.
6. Hand fixes: `work/hand1.py` (15 bare-noun definitions, ch. 17 orphan), `work/hand2.py` (broken `\index{}` keys, split
   `\texttt{}`, s20 orphan), `work/hand3.py` (20 overfull boxes), `work/hand4.py` (ten figure collisions), then by hand: the
   ch. 9 axis label, the ch. 24 problem title, three re-placements, the *rang IC* calque.
7. Contact sheet of all 87 figures, `pdfsweep.py`, final build into `build/`, sample.

## Lessons carried to Books 8–10

- Tables are where French overflows: an `l` column holding a row label, and multi-word headers. Give the first column a
  `p{}` width, and set `\tabcolsep` to 4pt inside the `center` group for near misses.
- A pgfplots legend with three columns of French entries runs out of the figure; one column is the safe default.
- `draft/pilot-quant-fr/overfull.py <log>` names the file and lines of every overfull box.
- `extra_report.py` now also flags English `Weekend problem` and `Part N` titles.
