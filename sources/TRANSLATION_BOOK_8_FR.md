# French pilot edition of One Quant Book 8 (`strategies-1`)

Part of the Books 6–10 run, `sources/TRANSLATION_BOOKS_6-10_FR.md` (one coordinator, no subagents). Score file
`translation_scores/book_8/fr/translation_score.md`.

| | |
|---|---|
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), 302 section calls, $2.14 list; coordinator `claude-opus-5-5` |
| Result | 88/100 (sampled), 356 pp, 0/0/0 under TeX Live 2026, `check_translation.sh` PASSED, linker `--check` 0 |
| Run directory | `draft/pilot-strategies-1-fr/` (`work/` holds this book's hand fixes and logs) |

## Steps as run

1. `run.py --workers 3` in the step-4 queue, 0 rejected.
2. `post.py`, `repair.py`, `post.py` again; NUMDIFF on 22 lines, all explained at line level.
3. `sites.py`, `install.py` (58 files); French tick labels in ch. 20.
4. Term links and census.
5. Shared sweeps in `draft/pilot-quant-fr/`: `fix_common.py` (with the *fiche de stratégie* agreement list),
   `typo_apply.py`, `dollars_apply.py` (no change), `crefart_apply.py` (no change), the three reports, `texttt_join.py`.
6. Hand fixes: `work/hand1.py` and `work/hand2.py` (bare definitions), `work/hand3.py` (table specs with
   `draft/pilot-quant-fr/tabspec.py`), then by hand: agreements, the ch. 14 Part title, stray articles, the ch. 29 index
   key, six figure collisions.
7. Contact sheet of all 57 figures, `pdfsweep.py`, sample, final build into `build/`.
8. Two checks found here and run back over Books 6 and 7: `iqroles_fr.py` (English roles in `\iqroles{}`) and
   `bare_lower_fix.py` (definitions opening on a lowercase bare noun). Books 6 and 7 were rebuilt into `build/`, still 0/0/0.

## Lessons carried to Books 9–10

- `\iqroles{}` arguments come back in English about one time in five; `draft/pilot-quant-fr/iqroles_fr.py <slug>` maps them.
- A bare-noun definition may start in lowercase as well as with a capital: search for a line starting `\emph{` whose
  previous line ends a `\label{}`, a sentence or a heading.
- A legend below the axis (`at={(0.5,-0.3)},anchor=north`) is the quick fix when French legend entries cover the data.
