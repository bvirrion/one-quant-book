# French pilot editions of One Quant Book 11–20: the run file

**Scope.** French (`fr`) editions of Books 11–20 (`hft`, `ml`, `low-latency`, `networks`, `platforms`, `desk`,
`industry`, `interviews-1`, `interviews-2`, `interviews-3`) by the pilot method of `../pilot_translation_instruction.md`.
Requested by the user 2026-11-11. Pilot tier: gates green, not read sentence by sentence, figures sampled, solutions
not recomputed.

| | |
|---|---|
| **Model** | `claude-haiku-5-5` (Haiku 5.5, effort medium), pilot method: one headless call per section; glossaries and coordinator `claude-opus-5-5` (Opus 5.5) |
| Run shape | **One coordinator at a time, no subagents of any kind.** Ten books, so two consecutive sessions (the method's five-book rule): session 1 does steps 1–3 for all ten books and closes Books 11–15; session 2, a fresh session, closes Books 16–20 |
| Terminology | As Books 1–10: French desk usage, English in parentheses at the definition |
| Expected usage (stated to the user before the run) | about 4–5 points of the weekly plan per five books, 8–10 for the run; pause and report past +7 points in one session |
| Usage, weekly plan (all models) | Session 1: 78 % at the start (2026-11-11 23:42, resets 2026-11-13 19:00); 78 % before step 4 (23:57); 79 % after Book 11 (2026-11-12 01:25); 80 % after Book 12; 80 % after Book 13 (02:21); 80 % after Book 14 (02:43); 81 % after Book 15 (03:29); 81 % at the session-1 close (03:45): **+3 points for session 1**, steps 1–3 of all ten books included Session 2: 82 % at the start (2026-11-12 09:13, resets 2026-11-13 19:00); 82 % after Book 16; 83 % after Book 17 (10:06); 84 % after Book 18 (10:23); 84 % after Book 19 (10:36); 84 % after Book 20 (10:46); 84 % at the session-2 close (11:05): **+2 points for session 2; 78 % → 84 % over the whole run, both sessions and the gap between them** |

## Set-up (steps 1–3, session 1, 2026-11-11/12)

- **Entry files** `one_quant_book_{11..20}_*_fr.tex`, built from the English entries with Book 10's French pattern
  (`\booklang`, French `\bookline`/`\bookhead`/`\title`, `colophon.fr`; `preface.fr` for Books 11–17, and
  `parts/interviews-N/fr/preface` for Books 18–20). `latexmkrc` and the CI release body list Books 11–15; Books 16–20
  join in session 2.
- **`styles/lang/fr.tex`**: the 30 part titles of Books 11–17 and the 9 of Books 18–20. The interview books printed
  their part titles literally (`\part{Speed}`); they now use `\omstr{part.iv1.speed}` etc., with the English in
  `styles/lang/en.tex` (English output unchanged).
- **`styles/ivbook.sty`** printed its UI strings in English (Answers, Follow-up, Classic wrong answer, Round, the stop
  line, Interviewer). They now go through `\iv@str{English}{French}`, which picks by `\booklang`.
- **Interview extras the pilot scripts don't translate** (`run.py` takes only `NN-*.tex`):
  - prefaces written by the coordinator into `parts/interviews-N/fr/preface.tex`;
  - `tools/make_interview_tracks.py interviews-N fr` writes `parts/interviews-N/fr/tracks.tex` (French headers and
    text, counts from the English tags, titles from the French chapters: run it after install);
  - `draft/pilot-quant-fr/ivgen_fr.py` writes `parts/interviews-N/generated/fr/`. The 131 drill-family strings went
    through one Haiku call (cached in `ivgen_fr.json`, math spans checked; one refusal fixed by hand), the
    `\text{ of }` words inside drill math through a fixed table. The French chapters' `\input{…/generated/…}` paths are
    switched after install.
- **Glossaries** `sources/GLOSSARY_BOOK_{11..17}_FR.md`: 1,223 lines written by the coordinator, one per English defined
  term (`glossary.py terms`), none already in Books 1–10. Books 18–20 define no terms, so their glossaries pin interview
  vocabulary as `00` lines (52, 35 and 47), with senses marked on *round*, *edge*, *width*, *queue*, *stack*, *heap*. Run
  glossaries `.run.md` by `draft/pilot-quant-fr/chain.py` (now Books 6–20); `glossary.py split` run for all ten.
  `draft/pilot-quant-fr/glossmake.py` assembles a glossary from `terms.txt` and the coordinator's lines.
- **Term configs** `tools/term_config/book{11..17}_fr.py` by `mkconfig.py`. Books 18–20 are not in the term linker in
  English either.
- **Series card** (`../pilot_translation/langs/series/one-quant-book.fr.md`): market making, ML, low-latency terms; the
  interview tags (`\iqroles`, `\iqfirm`, `\iqlevel`) as a fixed table; `la \cref{iq:…}`; the answers' headings; the
  S/B/P letters of the played games.
- **Step 4**: `draft/pilot-quant-fr/queue.sh <slugs>` (now takes the slugs), at most three `run.py --workers 3` at once,
  up to five passes per book, waiting on PIDs (`wait -n`); log `draft/pilot-quant-fr/queue.log`. Books 11–15 queued
  2026-11-11 23:57.

## Findings

- **Book 11** (88, 353 pp, 0/0/0, 239 calls, $1.90): `sources/TRANSLATION_BOOK_11_FR.md`.
- **Book 12** (88, 370 pp, 0/0/0, 291 calls, $2.47): `sources/TRANSLATION_BOOK_12_FR.md`. Two content losses found by
  NUMDIFF read per line (`numrun.py`, new); Fig. 3.1's labels in a local macro passed every gate in English.
- **Book 13** (88, 332 pp, 0/0/0, 405 calls, $3.08): `sources/TRANSLATION_BOOK_13_FR.md`. One section translated by the
  coordinator after failed retries (`save_hand.py`, new); Fig. 3.3's tick labels reversed because `ytick=data` follows
  the CSV's rows; Rust's *sound* first rendered *sûr*, which also means *safe*, so three links went to the wrong sense;
  an identifier allow block for Book 13 in `tools/check_latin_prose.py`.
- **Book 14** (88, 373 pp, 0/0/0, 304 calls, $2.25): `sources/TRANSLATION_BOOK_14_FR.md`. A handoff rendered three ways,
  one of them (*point d'échange*) an internet exchange point in French networking; cables drawn from a fixed x through the
  wider French node; *le long du géodésique* (feminine noun).
- **Ordinals without `\up{e}`** (found in Book 14's sample): *99e centile*. Fixed over every French book, `parts/*/fr/`
  **and `parts/*/solutions/fr/`** (the solutions are not under `fr/`): 80 ordinals in Books 2, 3, 6–9 and 11–14, plus
  `\up{e} centile` → `\up{e}~centile` in 25 files. Books 1–13 are rebuilt and re-gated at the session's close.
- **Book 15** (88, 395 pp, 0/0/0, 314 calls, $2.38): `sources/TRANSLATION_BOOK_15_FR.md`. 38 of 110 figures repaired
  for French text wider than the English layout (`figfix.py`); Rust *crates* as *caisses*; a Kafka offset as *position*
  next to the *service de positions*; symbolic coordinates translated by Haiku in four figures (the CSV keys must stay
  English).
- **Missing elision at a line break** (found in Book 15's openings): *le agrégateur*. New `elision_fr.py`, run over every
  French book: 37 fixed, three more by hand where Haiku had dropped a word.
- **Exercise items in the imperative** (Book 15's sample): *Énoncez le résultat nommé*. New `imperative_fr.py` (item heads
  only, lines with *vous* skipped), run over every French book: 36. `iq_imperative.py` still reports 0 afterwards.
- **Stray `=` lines** in displays (`eqline_fix.py`): 50 over Books 1, 5, 7, 8, 12–15. **Units** *MB/GB* → *Mo/Go*: 42.
  **Clock times** (`clock_fr.py`); `typo_apply.py` had put a `~` before the seconds of data timestamps, fixed in its mask.
  All three, and the two scripts above, are in `sweeps_all.sh`; every French book is rebuilt and re-gated at the close.
- New shared scripts: `sweeps_all.sh` (all step-6 fixers and reports for one book), `authors_et.py`, `numrun.py`,
  `save_hand.py` (a section translated by the coordinator, saved through `run.py`'s checks), `accept.py --keep-en`.
- **Interview questions in the infinitive** (found in Book 11's sample). They address the candidate, so French wants the
  imperative; Haiku writes the exercises' infinitive about one time in five. New `draft/pilot-quant-fr/iq_imperative.py`;
  **run back over Books 1–10: 143 lines**, plus 5 by hand where a pronoun inverts (*et l'utiliser* → *et utilisez-la*,
  *et en donner* → *et donnez-en*). Books 1–10 re-gated afterwards: `check_translation.sh` PASSED and linker `--check`
  clean for all ten (2026-11-12). The rule is in the series card.
- `bare_def_fix.py` (Book 11) dry-run over Books 1–10: nothing to fix.
- Series card: Book 11's lessons added before Books 16–20 are queued (imperative in interview questions, feminine
  heads *fiche*/*variable*/*cotation*, an article before an English desk noun opening a sentence).

- **Book 16** (88, 373 pp, 0/0/0, 251 calls, $2.14): `sources/TRANSLATION_BOOK_16_FR.md`. Session 2's first book. An invented
  row in solutions 15 (the momentum numbers under a second name), found by `numrun2.py` (new: `numrun.py` with moved numbers
  cancelled). Three new series-wide sweeps, in `sweeps_all.sh` and run back over every French book: `currency_fr.py`
  (`\euro`/`\pounds` before the amount: 49 in Books 1 and 9), `unitlabel_fr.py` (*\$ million* labels) and
  `bare_def_lower.py` (definitions opening on a bare lowercase noun: 48 over eleven books, Books 2–4 and 11–17). `sheet.py`
  missed captions printed beside the picture (chs. 28–30, an English layout defect, fixed in both languages); it now takes
  any caption that starts a line.
- **Book 17** (88, 361 pp, 0/0/0, 346 calls, $2.79): `sources/TRANSLATION_BOOK_17_FR.md`. Four sections rejected after
  the last pass were English that stays (names of filings and forms): `accept.py --english-ok`. The currency sweep had
  only ever moved `\$N$ millions de dollars`: `currency_fr.py` now moves every `\$` before an amount (33 here, 53 in
  Books 1, 3, 8, 9, 11 and 15), with math masked over the whole file. `invalid-in-math 2`, taken as a baseline in Books 9
  and 17, was `\euro` in math printing **£**: an English-canon defect, fixed in both languages with `\text{\euro}`. 30 CSV
  tick lists printed English keys (`figfr.py`); 14 figures repaired from the contact sheet.
- **Book 18** (88, 423 pp, 0/0/0, 248 calls, $2.00): `sources/TRANSLATION_BOOK_18_FR.md`. The first interview book.
  `ivgen_fr.py`'s family regex lacked `re.M`, so all 43 generated drill files kept English family names (fixed, re-run).
  Two gates misfired on the interview shape (a chapter with no answer file; French twin labels counted as duplicates):
  both patched. Four new series-wide sweeps in `sweeps_all.sh`: `tilde_thousands.py` (`60~000`, 7 lines in Books 1, 2,
  6, 14, 18), `answer_imperative.py` and `vous_imperative.py` (imperatives in answers → infinitive, 91 lines; its first
  version turned seven participles *faites* into *faire*, restored), `index_fr.py` (English `\index` entries, 24).
- **Book 19** (88, 383 pp, 0/0/0, 184 calls, $1.59): `sources/TRANSLATION_BOOK_19_FR.md`. **English canon: Books 18 and
  19 wrote thousands with a comma** (531 tokens), against `sources/INTERVIEW_BOOKS.md`; `comma_thousands.py` gives both
  languages a thin space (682 lines). Haiku translated one `\chapter` into `\chapitre` (`cmd_twin.py`, new, compares
  command names; no other in Books 1–19). The punctuation sweep had put `~:` into the generated tracks table's labels in
  Books 18 and 19, so its links were dead with no warning: `sweeps_all.sh` now makes the table last. `vous_imperative.py`
  now keeps `\ivsays` and quoted speech and knows the *-dre*/*-oir* verbs; its *-issez* rule had made *lair* of *laissez*.
- **Book 20** (88, 421 pp, 0/0/0, 193 calls, $1.79): `sources/TRANSLATION_BOOK_20_FR.md`. The code book: 399 listings
  untouched (gate 12). 17 overfull lines around unbreakable `\texttt` identifiers: `\emergencystretch` in the French entry
  took 14 of them. The answers' ch. 2 heading had kept the English title, which no check reads. `vous_imperative.py`
  learnt 17 more capitalised verbs and *parcourez*; `index_fr.py` four more entries; the prose gate now skips a tracks row
  identical in both languages (*C++*). Two chapter summaries of Book 19 still said *vous* (fixed by hand).

## Hand-over to session 2

**State at the end of session 1.** Books 11–15 are closed (score and run files, final builds in `build/`). Every
series-wide sweep of this session has been run over Books 1–15 and they were rebuilt and re-gated (see Close). Books
16–20 have had steps 1–3 (entry files, part titles, glossaries, configs, the interview extras of the set-up above);
their Haiku step 4 was queued in the background at 2026-11-12 02:51 (`queue.sh desk industry interviews-1
interviews-2 interviews-3`, log `draft/pilot-quant-fr/queue.log`). **Session 2 starts by reading `queue.log`**: if
it ends with `all done`, start step 5; if not, wait (never start a second `run.py` for a book still queued), and
re-queue only the books whose last pass left rejected sections.

**Queue result (2026-11-12 05:10, `all done`):** every file written for all five books (desk 60, industry 60,
interviews-1 65, interviews-2 42, interviews-3 18), no call stopped on a failure. Rejected sections after the last
pass: desk 0 (pass 2), interviews-1 0 (pass 3), interviews-2 0 (pass 3), interviews-3 0 (pass 5), **industry 3 files
after pass 5**: clear those first in session 2 (`accept.py` for an English line that should stay, otherwise `redo.py`,
then `save_hand.py` if Haiku still fails). No re-queue is needed.

**Session 2, for each of Books 16–20 in order** (`desk`, `industry`, `interviews-1`, `interviews-2`, `interviews-3`),
exactly as Books 11–15 (their run files show the commands):

1. Step 5: `post.py --units`, `repair.py`, `post.py`; `numrun.py` per line in the run directory; clear rejected
   sections with `accept.py`, or `redo.py` then `save_hand.py` for a section Haiku cannot do.
2. Step 6: `sites.py`; `install.py`; extend `FR_BOOKS` in `tools/termlink/books.py` (to 16, then 17) and run the
   linker `--apply` (Books 16–17 only; 18–20 are not in the linker); then `bash draft/pilot-quant-fr/sweeps_all.sh
   <slug>`. For Books 18–20 also, after install: `python3 draft/pilot-quant-fr/ivfix_fr.py interviews-N --apply` (the
   question tags as the card's fixed table, the `\input{…/generated/…}` paths pointed at `generated/fr/`, then
   `tools/make_interview_tracks.py interviews-N fr` for the tracks table; read the tags it lists rather than guesses),
   and `iq_imperative.py <slug> --apply` (its report must end at 0).
3. Step 7: `bash pilot_translation/build.sh one-quant-book <entry> draft/pilot-quant-fr/build-s2`; `overfull.py`; contact
   sheet of every captioned figure (`sheet.py`), crops of every repair (`figcrop_pdf.py`); `check_translation.sh <slug>
   fr` (and `tools/check_interview_book.py` for 18–20); `numfile.py`; `pdfsweep.py`.
4. Steps 8–9: `sample.py --n 20 --seed 1` plus three chapter openings; score file and per-book run file; a Findings
   bullet here; a usage reading (`claude -p /usage --tools ''`) after each book.

A new defect class becomes a script in `draft/pilot-quant-fr/`, joins `sweeps_all.sh`, and is run back over every
French book. **Close of session 2**: `latexmkrc` and the CI release body extended to Books 16–20; final builds of
Books 16–20 into `build/` (and of any earlier book a sweep changed); `check_translation.sh` over all twenty;
`one-quant-book/CLAUDE.md`, the root `CLAUDE.md` and `pilot_translation_instruction.md` updated; nothing committed.

**Prompt for session 2** (to paste into a fresh session started in `one-course/`):

> Read CLAUDE.md, pilot_translation_instruction.md, one-quant-book/CLAUDE.md, and
> one-quant-book/sources/TRANSLATION_BOOKS_11-20_FR.md (above all its "Hand-over to session 2" section), then the
> series card pilot_translation/langs/series/one-quant-book.fr.md and the run files of Books 11–15
> (one-quant-book/sources/TRANSLATION_BOOK_1{1..5}_FR.md). Then close the French pilot editions of One Quant Books
> 16–20 (desk, industry, interviews-1, interviews-2, interviews-3) from step 5 on, by the pilot method: you are the
> only coordinator, no subagents of any kind, at most three run.py at once, nothing committed, no dataset downloads.
> Measure usage with `claude -p /usage --tools ''` at the start and after each book; pause and report past +7 points.

## Close

**Session 1 close (2026-11-12 03:45)**, `draft/pilot-quant-fr/close_s1.sh`, log `close_s1.txt`:

- **Final French builds into `build/`**, TeX Live 2026, all 0 errors / 0 undefined / 0 overfull: Books 1–10 at their
  recorded page counts (403, 393, 354, 372, 366, 343, 370, 356, 356, 327) after this run's series-wide sweeps; Book 11
  353 pp, Book 12 370, Book 13 332, Book 14 372 (373 before the sweeps), Book 15 395.
- **Regression, English Books 11–20** in scratch (`draft/pilot-quant-fr/build-en-s1/`): all 0/0/0 at the table's page
  counts (329, 348, 314, 349, 367, 347, 339, 393, 348, 391), so the shared style, string and part-title changes left the
  English unchanged.
- **`check_translation.sh <slug> fr` PASSED and linker `--check` clean for all fifteen French books.**
- Usage: see the table at the top. Nothing committed.

**Session 2 close (2026-11-12 11:05)**, `draft/pilot-quant-fr/close_s2.sh`, log `close_s2.txt`:

- **Final French builds of all twenty books into `build/`**, TeX Live 2026, all 0 errors / 0 undefined / 0 overfull
  (session 2's series-wide sweeps touched Books 1–17): Books 1–15 at their recorded page counts (403, 393, 354, 372,
  366, 343, 370, 356, 356, 327, 353, 370, 332, 372, 395), Book 16 373, Book 17 361, Book 18 423, Book 19 383, Book 20
  421.
- **Regression, English Books 9 and 16–20** in scratch (`draft/pilot-quant-fr/build-en-s2/`): all 0/0/0 at the table's
  page counts (333, 347, 339, 393, 348, 391), after the canon fixes (`\text{\euro}` in Books 9 and 17; `\,` thousands
  in Books 18 and 19) and the tools changes.
- **`check_translation.sh <slug> fr` PASSED for all twenty French books**; linker `--check` clean for Books 1–17;
  `check_interview_book.py --final` and `--cross` GREEN for Books 18–20.
- Docs: `one-quant-book/CLAUDE.md`, the root `CLAUDE.md`, `pilot_translation_instruction.md` (Books 16–20 lessons) and
  the series card updated. Nothing committed.

