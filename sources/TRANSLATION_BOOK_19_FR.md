# French pilot edition of One Quant Book 19 (`interviews-2`)

Part of the Books 11–20 run, `sources/TRANSLATION_BOOKS_11-20_FR.md` (one coordinator, no subagents; session 2 closes
Books 16–20). Score file `translation_scores/book_19/fr/translation_score.md`.

| | |
|---|---|
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), 184 section calls, $1.59 list; coordinator `claude-opus-5-5` |
| Result | 88/100 (sampled), 383 pp, 0/0/0 under TeX Live 2026, `check_translation.sh` PASSED, `check_interview_book.py --final` and `--cross` GREEN |
| Run directory | `draft/pilot-interviews-2-fr/` (logs, sample, `pdfsweep.txt`, `numrun.txt`, `numfile.txt`, `fixes.py`) |

## Steps as run

1. `run.py --workers 3` in the step-4 queue (session 1): 0 rejected after pass 3.
2. `post.py --units`, `repair.py`, `post.py` (`step5.sh`); `numrun2.py` in the run directory (628 lines: the decimal
   commas and the English comma thousands, below).
3. `sites.py` (0 lines), `install.py` (42 files); `ivfix_fr.py interviews-2 --apply`, which stopped in the tracks script
   on a translated `\chapitre`; fixed, tracks made again; `iq_imperative.py` (0 left).
4. `comma_thousands.py interviews-1 --apply` and `interviews-2 --apply` (English canon and French twins), before
   `sweeps_all.sh interviews-2`, so that `fix_common.py` could tell a French decimal comma from an English thousands one.
5. `vous_imperative.py all --apply` again after its repairs (`\ivsays`, quoted speech, irregular verbs, the *-issez* rule).
6. Build (6 overfull), `fixes.py`, the tracks generator's French column; build 0/0/0; both gates; `numfile.py`;
   `pdfsweep.py`; sample; three chapter openings (chs. 4, 12, 19); a last build and both gates again.

## Lessons

- **Check the English against the series rules before translating it.** Books 18 and 19 were written after the
  2026-09-29 thousands sweep and brought comma thousands back (531 tokens); in French each one reads as a decimal.
  A sweep that tells decimal from thousands by comparing with the English (`fix_common.py`) is blind when the English
  uses the same character for the other job.
- **Generated files must be generated after the sweeps.** The tracks table's labels were damaged by a punctuation
  sweep in Books 18 and 19, and nothing reported it: a dead `\hyperref` leaves no warning the build summary counts.
- **The model can translate a command name.** `\chapitre` passed the structure check (which compares environments and
  labels) and built without error until a script looked for `\chapter`. `cmd_twin.py` now compares command names.
- **A suffix rule needs a word list, not a suffix.** *-issez* → *-ir* is right for *choisissez* and wrong for
  *laissez*; the sweep now converts only listed *-ir* verbs.
