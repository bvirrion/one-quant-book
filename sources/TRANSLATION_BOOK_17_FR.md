# French pilot edition of One Quant Book 17 (`industry`)

Part of the Books 11–20 run, `sources/TRANSLATION_BOOKS_11-20_FR.md` (one coordinator, no subagents; session 2 closes
Books 16–20). Score file `translation_scores/book_17/fr/translation_score.md`.

| | |
|---|---|
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), 346 section calls, $2.79 list; coordinator `claude-opus-5-5` |
| Result | 88/100 (sampled), 361 pp, 0/0/0 under TeX Live 2026, `check_translation.sh` PASSED, linker `--check` 0 |
| Run directory | `draft/pilot-industry-fr/` (logs, sample, `sheet/`, `crops/`, `pdfsweep.txt`, `numrun.txt`, `figfr.py`, `fixes.py`, `fixes2.py`, `figfix.py`, `figfix2.py`, `samplefix.py`) |

## Steps as run

1. `run.py --workers 3` in the step-4 queue (session 1): 3 files with a rejected section after the last pass. Session 2
   read each flagged line: all four were English that stays (names of filings and forms), so `accept.py <ch> course
   <section> --english-ok <line> --save`, then a `run.py` pass that reported 0 rejected.
2. `post.py --units`, `repair.py`, `post.py` (`draft/pilot-quant-fr/step5.sh`); `numrun2.py` in the run directory, with
   six number repairs before install.
3. `sites.py` (49 lines, all figure code read on the contact sheet), `install.py` (60 files); `FR_BOOKS` extended to 17;
   term links `--apply` (873).
4. `sweeps_all.sh industry`, which now also prints the PREFIX LEAK report (below).
5. Hand fixes: `figfr.py` (30 CSV tick lists and two `\foreach` lists in French), `fixes.py` and `fixes2.py` (tables,
   axis widths, the ch. 14 title), `figfix.py` and `figfix2.py` (14 figures), the Book 17 block in
   `tools/check_latin_prose.py`, `samplefix.py` (the sample and the chapter openings).
6. New or extended series-wide sweeps, run back over every French book: `currency_fr.py` now moves `\$` too (53 lines
   in Books 1, 3, 8, 9, 11 and 15), `unitlabel_fr.py` takes *\$ milliers* (2 in Books 11 and 15), `imperative_fr.py`
   has a longer verb list (3 in Books 3 and 13, by hand where the verb was coordinated).
7. Contact sheet of all 86 figures; crops of every repair; sample; three chapter openings; `pdfsweep.py`.

## Lessons

- **A narrow sweep looks like a rule kept.** `dollars_apply.py` moved only `\$N$ millions de dollars`; every other
  `\$157\,698` stayed in front of its number in six books, though the series card has asked for the currency after
  the amount since Book 1. A sweep needs to be tested against the rule it enforces, not against the pattern it was
  written for.
- **Math that spans lines defeats a per-line mask.** The first `\$` rule turned `…=\$6.00$` into `…6.00~\$$` wherever a
  `$…$` opened on the line above. `currency_fr.py` now masks math over the whole file.
- **A baseline warning can be a defect.** `invalid-in-math 2` appeared in the English and French builds of Books 9 and
  17 and was taken as harmless; it was `\euro` in math, which prints **£**. Read what a baseline warning prints before
  accepting it.
- **A stray prefix can stop a build.** One table row came back from the model with `1=` at its start, which its English
  twin does not have (*Misplaced \omit*). `sweeps_all.sh` now reports any line starting `N=` or `N|` whose twin does not.
- **Pay tables put the currency in each cell** (Table 12.1 mixes dollars, euros and pounds): the sweep must not move a
  currency to the header, and the header must not name one.
