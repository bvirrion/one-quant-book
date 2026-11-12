# French pilot edition of One Quant Book 18 (`interviews-1`)

Part of the Books 11–20 run, `sources/TRANSLATION_BOOKS_11-20_FR.md` (one coordinator, no subagents; session 2 closes
Books 16–20). Score file `translation_scores/book_18/fr/translation_score.md`.

| | |
|---|---|
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), 248 section calls, $2.00 list; coordinator `claude-opus-5-5` |
| Result | 88/100 (sampled), 423 pp, 0/0/0 under TeX Live 2026, `check_translation.sh` PASSED, `check_interview_book.py --final` and `--cross` GREEN |
| Run directory | `draft/pilot-interviews-1-fr/` (logs, sample, `sheet/`, `crops/`, `pdfsweep.txt`, `numrun.txt`, `fixes.py`) |

## Steps as run

1. `run.py --workers 3` in the step-4 queue (session 1): 0 rejected after pass 3.
2. `post.py --units`, `repair.py`, `post.py` (`draft/pilot-quant-fr/step5.sh`); `numrun2.py` in the run directory.
3. `sites.py`, `install.py` (65 files); `ivfix_fr.py interviews-1 --apply` (192 lines; it also runs
   `tools/make_interview_tracks.py interviews-1 fr`); `iq_imperative.py` (0 left); `ivgen_fr.py` re-run after its fix
   (43 generated files).
4. `sweeps_all.sh interviews-1`, now with `tilde_thousands`, `answer_imperative`, `index_fr` and `vous_imperative`.
5. Hand fixes: `fixes.py` (five `sloppypar` wraps, ch. 19's header, Fig. 7), four TeX-accent repairs, *Jules César*.
6. Build, `overfull.py`, contact sheet (11 figures), crop of Fig. 7, the two gates, `numfile.py`, `pdfsweep.py`, sample,
   three chapter openings (chs. 9, 15, 22), a last rebuild and both gates again.

## Lessons

- **A regex without `re.M` silently matches nothing.** `ivgen_fr.py` anchored its family pattern with `$` and no
  multiline flag, so every generated drill kept its English family name while the script reported success. It printed
  "wrote 43 files" both times; only the PDF sweep showed the difference.
- **Gates written for one shape of book misfire on another.** `check_translation.sh` flagged a chapter with no English
  answer file as "solutions missing", and `check_interview_book.py` counted every French twin label as a duplicate.
  Both now skip what has no English twin, or sits in a language subdirectory.
- **Answers need the infinitive everywhere, not only at line start.** `answer_imperative.py` caught 21 lines; the
  answers' running imperatives (*… puis vérifiez …*, *N'oubliez pas*) needed `vous_imperative.py`, which moves enclitic
  pronouns and the negation. **Its first version turned the participle *faites* into *faire*** (seven lines over five
  books: *les écritures faire avant le release*). It now converts *faites*/*dites* only when capitalised, and the seven
  were restored by hand. A sweep that rewrites a homograph needs a rule for the other reading.
- **A label quoted in a question must be quoted the same way in its answer** (*«~mixte~»* / *«~mélange~»*, ch. 16):
  the model translates the two files apart. Nothing sweeps this yet; the PDF sweep led to it.
