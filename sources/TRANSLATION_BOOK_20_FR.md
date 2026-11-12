# French pilot edition of One Quant Book 20 (`interviews-3`)

Part of the Books 11–20 run, `sources/TRANSLATION_BOOKS_11-20_FR.md` (one coordinator, no subagents; session 2 closes
Books 16–20). Score file `translation_scores/book_20/fr/translation_score.md`.

| | |
|---|---|
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), 193 section calls, $1.79 list; coordinator `claude-opus-5-5` |
| Result | 88/100 (sampled), 421 pp, 0/0/0 under TeX Live 2026, `check_translation.sh` PASSED, `check_interview_book.py --final` and `--cross` GREEN |
| Run directory | `draft/pilot-interviews-3-fr/` (logs, sample, `pdfsweep.txt`, `numrun.txt`, `numfile.txt`, `fixes.py`) |

## Steps as run

1. `run.py --workers 3` in the step-4 queue (session 1): 0 rejected after pass 5.
2. `post.py --units`, `repair.py`, `post.py` (`step5.sh`); `numrun2.py` in the run directory (115 lines).
3. `sites.py` (0 lines), `install.py` (18 files), `cmd_twin.py` (0), `ivfix_fr.py interviews-3 --apply` (110 lines,
   tracks), `iq_imperative.py` (0 left).
4. `sweeps_all.sh interviews-3`; `vous_imperative.py` extended (verbs, *parcourez*, *faites* + infinitive) and run again
   over every book (19 lines).
5. Build (17 overfull): `\emergencystretch` in the French entry, then `fixes.py` for the three left; the solutions 2
   heading by hand; the prose gate taught to skip a tracks row; `index_fr.py` extended and run over every book.
6. Both gates, `numfile.py`, `pdfsweep.py`, sample, three chapter openings (chs. 2, 7, 8); a last build and both gates.

## Lessons

- **Code-heavy French needs line stretch, not paragraph wraps.** Seventeen overfull lines came from unbreakable
  `\texttt` identifiers in longer French sentences; `\emergencystretch` in the French entry removed fourteen with no
  change to the text, against one `sloppypar` per paragraph in Books 11–19.
- **An answer-file heading is a title too.** The solutions file's `\section*` and `\markboth` carry the chapter title;
  Haiku left one in English, and neither the structure check nor `HEADING_EN` (which reads `\chapter` only) looks there.
- **A chapter summary that addresses the reader slips into *vous*.** The card asks for *on* or the infinitive in
  `ivtrains`; `vous_imperative.py` skips any line with *vous*, so those lines need reading (two here, two in Book 19).
