# French pilot edition of One Quant Book 10 (`microstructure`)

Part of the Books 6–10 run, `sources/TRANSLATION_BOOKS_6-10_FR.md` (one coordinator, no subagents). Score file
`translation_scores/book_10/fr/translation_score.md`.

| | |
|---|---|
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), 359 section calls, $2.42 list; coordinator `claude-opus-5-5` |
| Result | 88/100 (sampled), 327 pp, 0/0/0 under TeX Live 2026, `check_translation.sh` PASSED, linker `--check` 0 |
| Run directory | `draft/pilot-microstructure-fr/` (`work/` holds this book's hand fixes and logs) |

## Steps as run

1. `run.py --workers 3` in the step-4 queue, 0 rejected; more repairs than any other book (359 calls for 114 sections).
2. `post.py`, `repair.py`, `post.py` again. One line came back in English (ch. 16:370) and was split into French by hand.
3. `sites.py`, `install.py` (56 files).
4. Term links (1,017) and census.
5. Shared sweeps in `draft/pilot-quant-fr/`: `fix_common.py`, `typo_apply.py`, `dollars_apply.py`, `crefart_apply.py`
   (3, after the sample), `iqroles_fr.py`, `texttt_join.py`, `wkend_labels.py`, `quotes_fr.py` (none left), the reports,
   and the new `index_join.py` for `\index{}` keys split across a line end.
6. Hand fixes: English headings and Part titles, the prose gate's fragments, bare definitions, stranded articles, a
   duplicated line; `work/hand3.py` (five tables, the ch. 2 TikZ text); six figure collisions.
7. Contact sheet of all 70 figures, crops of the repaired ones, `pdfsweep.py`, sample, `numfile.py`. The final build went
   into `build/` at the close of the run.

## Lessons

- Read the sample for the mid price: Haiku wrote *point médian* or *cours médian* ("median"). The glossary had *prix
  milieu* for *mid price* only. Bare *mid* now needs a line in the series card.
- A key split across a line end breaks `\index{}` the same way it breaks `\texttt{}`. `index_join.py` joins it.
