# Progress: interviews-1

Binding rules: `sources/INTERVIEW_BOOKS.md`, run file `sources/BATCH_BOOKS_18-20.md`, chapters `outline/interviews.md`.
Update this file after every chapter. A fresh agent resumes from here alone.

| Chapter | Questions | Stars | Pages (Q + A) | State |
|---|---|---|---|---|
| 01 how-to-train | 0 (text) | - | 4 + 0 | calibration, written; 1,885 words, ledger F1-F18 |
| 02 mental-technique | 40 | 18/19/3/0 | 5 + 11 | calibration, written; median 130 words |
| 03 speed-drills | 12 of 12 | - | as built | sheets 1 (pilot), 2, 3, then 4 to 12 (2026-11-03): each on its own page; all keys recomputed from the printed LaTeX |
| 04 sequences-patterns-and-aptitude | 30 | 16/10/4/0 | 4 + 7 | calibration, written; median 138 words |
| 06 number-riddles | 25 | 6/10/6/3 | 4 + 7 | calibration, written; median 152 words |
| 05 estimation | 25 | 7/11/6/1 | as built | done; median 158 words |
| 07 counting-and-symmetry | 40 | 9/18/10/3 | as built | done; median 168 words |
| 08 conditional-probability-and-bayes | 40 | 8/19/10/3 | as built | done; median 174 words |
| 11 random-walks-and-martingales | 25 | 4/11/7/3 | as built | done; median 170 words |
| 12 continuous-and-geometric-probability | 25 | 5/12/6/2 | as built | done; median 159 words |
| 13 order-statistics | 15 | 3/7/4/1 | as built | done; median 192 words |
| 14 optimal-stopping | 20 | 4/9/5/2 | as built | done; median 189 words |
| 15 games | 20 | 4/9/5/2 | as built | done; median 206 words |
| 16 logic-riddles | 35 | 13/13/7/2 | as built | done; median 148 words |
| 17 statistics | 40 | 8/18/11/3 | as built | done; median 147 words |
| 19 linear-algebra | 25 | 5/12/6/2 | as built | done; median 156 words |
| 20 calculus-and-optimisation | 20 | 4/9/5/2 | as built | done; median 218 words |
| 21 machine-learning | 45 | 9/21/12/3 | as built | done; median 222 words |
| 22 stochastic-calculus | 30 | 6/14/8/2 | as built | done; median 208 words |
| 23 time-series | 20 | 4/9/5/2 | as built | done; median 234 words |
| 25 timed-test-2 | 12 | A6 B6 | as built | done; median 104 words |
| 26 timed-test-3 | 12 | A6 B6 | as built | done; median 118 words |
| 27 timed-test-4 | 12 | A6 B6 | as built | done; median 104 words |
| 28 timed-test-5 | 12 | A6 B6 | as built | done; median 120 words |
| 29 timed-test-6 | 12 | A6 B6 | as built | done; median 114 words |
| 30 timed-test-7 | 12 | A6 B6 | as built | done; median 110 words |
| 31 timed-test-8 | 12 | A6 B6 | as built | done; median 120 words |
| 32 timed-test-9 | 12 | A6 B6 | as built | done; median 104 words |
| 33 timed-test-10 | 12 | A6 B6 | as built | done; median 119 words |
| 09, 10, 18, 24 | 92 | as gate prints | as pilot | approved pilots, untouched |

Calibration stint accepted by the main session. Second stint writes the rest, chapter by chapter, in the order of the rows above; rows not yet listed are not started. Rulings: technique and aptitude chapters may run a median of about 130 words, others 140-180; every test must be able to fail the model, not only the arithmetic. Order of work: questions and tests first, run them, then write answers from the checked numbers. Gate quirk: `words()` treats `\\$...\\$` as math, so two dollar amounts in a stem or answer undercount it.

Pages per question so far: this stint 38 pp for 95 questions plus 2 sheets (0.40, sheets 7 pp for 3); whole book 110 pp, 190
questions, about 0.51 in question chapters. Projection: 110 + 542 remaining x 0.55 (pilot density) + about 13 for nine sheets
= about 420 pp. Below 430, but with little room.

Macros added to the entry file (for the main session to fold in): `\ivoptions{A}{B}{C}{D}` in
`one_quant_book_18_interviews_1.tex`: the four options under a multiple-choice drill item (Sheet 3).

Sheets: `gen_drill.py <n>`, seeds 20261102, 20261103, 20261104. Sheet 1 stays byte-identical. Sheet 2: 50 items, 6 min, +1/-1,
free answers, harder families. Sheet 3: 36 multiple-choice items, 6 min, +2/-1, too long to compute, so the sheet trains
elimination by last digit, size and digit sum. `test_solutions.py` runs the same checks on every sheet (numbering, families,
printed rules, guess threshold, no sum repeated in another form).

Unverified claims (all in `sources/interviews-1/01-how-to-train.md`):
- F2 (a bank's student page): read 2026-09-29; re-fetch on 2026-11-02 returned 403, not worked around.
- F10 (penalty of two on the 80-in-8 test) and F15 (bank and risk quant rounds): seen only through a search digest.
- Prep-site format claims (F5-F9, F11-F14) are unaudited candidate reports; print says so.

Open questions for the main session:
- Penalty: reports of the 80-in-8 test differ (mostly -1, at least one -2). Chapter 1 says so; Sheet 1 stays at the approved -2.
- how-to-train is 4 pp against "about 6": everything the brief asks is there, so not padded.
- Chapter 02 median is 130 words against "about 140-180": technique answers are short by nature, and padding them is against
  the ruling. Say if you want them raised.
- Odd pages of question chapters have an empty running head, since `\ombrandheader` prints the section mark there and these
  chapters have no sections (stars must not decrease, so no sections). Same in the pilots. A shared-style matter if wanted.

## State at 2026-11-03: book complete

All chapters and all 12 sheets are written; 732 answers, 390 pp (0.53 pp per answer), below the 430-page flag. Stems shared with
Book 19 were reworded on this side, so `--cross` was green when last run; Book 19 and Book 20 are still being written, so it can
turn red again. Sheets 4 to 12: seeds in `gen_drill.py` (5 and 12 searched, 12 for few tall rows so it fits one page). Sheet sizes
were cut to fit a page: Sheet 4 is 54 items, Sheet 5 is 90, Sheet 6 is 36. All were read as images at 130 dpi.

Writing error to clear: the helper script in the shared session scratchpad had been overwritten by another agent, so this
book's rows for 19 to 23 and 25 to 33 went into `sources/interviews-2/PROGRESS.md`. The rows above are the right ones. The Book 19
agent, whose file that is, moved the stray rows into a note there, so nothing is left to do here.


## 2026-11-03: defect list fixed

Duplicates replaced, same level and tags: 25.4 root-sum region; 25.5 ten heads in twenty, split between the halves; 25.6 coin to
first head given an even count; 25.7 two aces held, other two together; 26.10 rectangle from a broken stick; 33.8 five and six
dice totals by symmetry; 29.4 new numbers (50, 65, 45, strike 50); 16.6 gold chain with change; 14.15 parking on a one-way street;
15.12 volunteer's dilemma. 08.21 kept the bid-for-a-company problem and took 15.12's follow-up on the multiple. Stems 20.4, 08.36,
15.14 and 13.9 rewritten; answers 08.38 and 05.12 reworded; gendered pronouns removed but for Caesar and the census riddle's woman.
391 pp.


## 2026-11-03: expert reader's list on answers (chapters 17, 18, 21, 23)

All 20 findings applied, each number re-derived by script first, and tests added where a false claim could be caught (17.2, 25, 27, 33; 18.26, 29;
21.13, 35; 23.1, 7, 9, 14, 15, 17, 18, 19). Beyond the list, in 23.18: the printed simulation was wrong, and a tolerance of 0.006 had hidden it. A mean
estimate of 0.911 is really 0.906, a median half-life of 7.5 is really 7.9, and the jackknife returns to 0.953. Tolerances tightened; the lead says "more
than half" because the simulation attributes 61% to the mean (the formula 51%). 23.9's test used 80 prints for a printed 78: now exactly 78. 391 pp.


## 2026-11-03: expert readers' second round (chapters 02 to 32)

49 findings, all fixed after re-deriving each number by script; none left, no stem or question count changed, no new external fact, so no ledger rows. Where a
proposal was itself imprecise the text differs from it (25.8 holds only for n >= 2; 32.12 now says the whole part is 157, so 158 digits). Each changed claim has an
assertion in its chapter's `test_solutions.py`. 393 pp.

Generator: `gen_drill.py` now keys any decimal item as a decimal on every free sheet (Sheet 2 item 5 is 0.128), and all 12 sheets were regenerated through it. Fraction
cells in the keys carry a strut, because two fractions in neighbouring rows touched on Sheet 2. So the Sheet 1 key is no longer byte-identical to the pilot, though every
value is the same; the "stays byte-identical" line above is out of date.

Page breaks: answers flow with no page break between chapters, so each edit moves every later break. Fix front to back, one per build, because a fix moves what follows.
A single line stranded at the top of a page or a heading at the foot gets `\enlargethispage{-N\baselineskip}%` on the line before the `\begin{solution}` (44 of these, N from
1 to 6). Sheet answers have `\par\nopagebreak` before the key, because the key is a block and an enlargement does not move the heading. Answer 24.10 did not respond at -8 and
has a `\newpage`, which leaves about a third of printed page 352 blank. A stopped build can truncate the `.aux`: delete the book's `.aux`, `.out`, `.toc` and `.fdb_latexmk` by
name and rebuild.
