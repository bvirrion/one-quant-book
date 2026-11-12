# French pilot edition of One Quant Book 13 (`low-latency`)

Part of the Books 11–20 run, `sources/TRANSLATION_BOOKS_11-20_FR.md` (one coordinator, no subagents; session 1 closes
Books 11–15). Score file `translation_scores/book_13/fr/translation_score.md`.

| | |
|---|---|
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), 405 section calls, $3.08 list; coordinator `claude-opus-5-5` |
| Result | 88/100 (sampled), 332 pp, 0/0/0 under TeX Live 2026, `check_translation.sh` PASSED, linker `--check` 0 |
| Run directory | `draft/pilot-low-latency-fr/` (logs, sample, `sheet/` and `sheet2/`, `crops/`, `pdfsweep.txt`, `fixes.py`, `work/ch23s1.fr.tex`) |

## Steps as run

1. `run.py --workers 3` in the step-4 queue: 18 files with a rejected section after pass 1, then 8, 8, 5, 5. Most
   cleared with `redo.py` or `accept.py` (drawing code flagged as English). Ch. 23 §1 failed every retry, truncating or
   duplicating `\texttt` spans, and the last reply overwrote better ones; the coordinator translated it
   (`work/ch23s1.fr.tex`) and saved it through `run.py`'s checks with `save_hand.py` (new).
2. `post.py`, `repair.py`, `post.py`; `numrun.py` per line in the run directory found six lines to fix before install
   (a dropped clause in solutions 4, misplaced percentile ordinals in ch. 26).
3. `sites.py`, `install.py` (52 files); `FR_BOOKS` extended to 13; term links `--apply` (820, then 817).
4. `sweeps_all.sh low-latency`. `typo_apply.py` crashed on a line ending in a control space (`\ `); fixed (`re.S`) and
   rerun.
5. Hand fixes: the 44 `sites` lines (figure labels, `\foreach` label lists, pgfplots tick lists that print a symbolic
   coordinate), four bare definitions, one English heading, the prose gate's identifier labels (an allow block for
   Book 13 in `tools/check_latin_prose.py`), 14 overfull boxes (`fixes.py`), 23 figure collisions.
6. Contact sheet of all 73 figures, twice; crops of the last repairs; sample; three chapter openings; `pdfsweep.py`.

## Lessons

- **`ytick=data` (or `xtick=data`) orders the ticks by the CSV's rows, not by `symbolic coords`.** A translated
  `yticklabels={…}` list must follow the data file's row order. Fig. 3.3 printed *même ligne* on the fastest bar. Check
  each translated tick list against its CSV (`cut -d, -f1`).
- **A glossary word that is also an everyday word links in the wrong sense.** *sûr* for Rust's *sound* also means *safe*,
  so the linker tied *interface sûre* and *bascule sûre* to the definition. Pick a term that is not a common adjective
  of the same field (*sain*), and mark the glossary line.
- **A pathological section can cost more in retries than by hand.** After two failed `redo.py` calls on the same
  section, translate it yourself and save it with `save_hand.py`; it runs the same checks.
- Code-heavy chapters print identifiers as chart labels in every language. Allow the exact tokens in the prose gate
  under a per-book comment rather than wrapping them in `\texttt` (which would break the code twin gate).
- A `\foreach \a/\b in {…}` over node names prints nothing but trips the twin gate; write the `\draw`s out.
- Long `\texttt` in prose: `\sloppy` appended to the enclosing `solution`/`enumerate`/`tutsteps` line keeps the line
  count; a plain paragraph takes `sloppypar`.
