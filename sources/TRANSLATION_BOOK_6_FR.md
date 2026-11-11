# French pilot edition of One Quant Book 6 (`rates-credit-risk`)

Part of the Books 6–10 run, `sources/TRANSLATION_BOOKS_6-10_FR.md` (one coordinator, no subagents). Score file
`translation_scores/book_6/fr/translation_score.md`.

| | |
|---|---|
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), 313 section calls, $2.28 list; coordinator `claude-opus-5-5` |
| Result | 88/100 (sampled), 343 pp, 0/0/0 under TeX Live 2026, `check_translation.sh` PASSED, linker `--check` 0 |
| Run directory | `draft/pilot-rates-credit-risk-fr/` (`work/` holds this book's hand fixes and logs) |

## Steps as run

1. `run.py --workers 3` in the step-4 queue: 3 passes, 0 rejected.
2. `post.py`, `repair.py` (18 sites), `post.py` again; NUMDIFF on 13 files, all explained at line level.
3. `sites.py`, `install.py`; `work/figfix.py` (French `xticklabels`/`yticklabels` for 15 figures).
4. Term links: `--unwrap --apply`, `--apply`, census.
5. Shared sweeps in `draft/pilot-quant-fr/`: `fix_common.py`, `typo_apply.py`, `dollars_apply.py`, `crefart_apply.py` (each
   change read), `sweep_report.py`, `lens_report.py`, `shift_report.py`, `extra_report.py`.
6. Hand fixes: `work/hand1.py` (bare-noun definitions, a doubled *et*, a `\cref` article), `work/hand2.py` (ch. 19 bar labels,
   ch. 17 and 20 line alignment, s28 duplicate, ch. 7 index key, *Société Générale*), `work/hand3.py` (overfull boxes, ch. 24
   `\chaptermark`), then by hand: four figure collisions, ch. 8 line, the five sample findings.
7. Contact sheet of all 107 figures, `pdfsweep.py`, final build into `build/`, sample.

## Lessons carried to Books 7–10

- `build.sh`'s third argument must be absolute: the script `cd`s into the repo first, so a relative outdir builds into a
  nested `one-quant-book/one-quant-book/…` and the summary reads that copy. (One such nested build was made here and deleted
  file by file.)
- A label anchored beside a dashed marker can land on the curves once French makes it longer; read every such label.
- A ch. 2 term (*cash*) can be translated by a word that is also a technical term elsewhere (*numéraire*); the sample found
  it, no gate can.
