# Progress: interviews-2

Binding rules: `sources/INTERVIEW_BOOKS.md`, run file `sources/BATCH_BOOKS_18-20.md`, chapters `outline/interviews.md`.
Update this file after every chapter. A fresh agent resumes from here alone.

| Chapter | Questions | Stars | Pages | State |
|---|---|---|---|---|
| 01 betting-and-kelly | 35 of 35 | 10/15/8/2 | about 16 | done: gate, ruff, 35 tests, 0/0/0 |
| 02 making-a-market | 35 of 35 | 7/15/10/3 | about 19 | done, accepted |
| 03 played-games | 12 of 12 | 0/0/0/12 | about 27 | done: 12 games, 12 tests + table check; no external facts; score sheets read at 130 dpi |
| 04 options-and-bond-arithmetic-at-speed | 25 of 25 | 12/11/2/0 | about 10 | done: 25 tests |
| 05 markets-and-microstructure | 50 of 50 | 15/19/13/3 | about 22 | done: 50 q, 46 tests + 4 NONNUMERIC |
| 06 etfs-futures-and-index-arbitrage | 35 of 35 | 9/15/9/2 | about 16 | done: 35 tests; two commonplaces flagged unverified in the ledger |
| 07 options-parity-and-greeks | 50 of 50 | 14/20/13/3 | about 20 | done: 50 tests |
| 08 pricing-and-numerics | 50 of 50 | 13/19/15/3 | about 24 | done: 50 tests |
| 09 vol-surface-and-vol-trading | 40 of 40 | 9/16/12/3 | about 18 | done: 39 tests + 1 NONNUMERIC |
| 10 rates-and-fx | 50 of 50 | 13/20/14/3 | about 19 | done: 50 tests |
| 11 credit-and-xva | 20 of 20 | 5/8/6/1 | about 11 | done: 20 tests; three rows reused, commonplaces flagged in the ledger |
| 12 commodities-and-energy | 20 of 20 | 5/8/6/1 | about 10 | done: 20 tests; three rows reused |
| 13 risk-validation-and-regulation | 40 of 40 | 10/15/12/3 | about 17 | done: 39 tests + 1 NONNUMERIC; 8 rows reused, F9 read from d457 at MAR33.4 |
| 14 crypto-for-traders-and-researchers | 30 of 30 | 8/11/9/2 | about 14 | done: 30 tests (1 hour-step AMM simulation, 6 s); 3 rows reused; no venue named in print |
| 15 portfolio-construction | 25 of 25 | 6/11/7/1 | about 11 | done: 25 tests; four rows reused |
| 16 macro-market-knowledge-and-pitches | 25 of 25 | 7/10/7/1 | about 10 | done: 20 tests + 5 NONNUMERIC; 4 rows reused; no market level, no company in print |
| 17 valuation-and-financial-statements | 25 of 25 | 7/11/5/2 | about 13 | done, accepted |
| 18 research-and-strategy-cases | 40 of 40 | 10/16/11/3 | about 16 | done: 38 tests + 2 NONNUMERIC; 3 rows reused |
| 19 behavioural-and-fit | 30 of 30 | 14/12/4/0 | about 14 | done, accepted |
| 20 your-strategy-and-your-project | 20 of 20 | 5/8/6/1 | about 9 | done: 12 tests + 8 NONNUMERIC; no rows, commonplaces flagged |
| 21 mock-interviews | 10 of 10 | 0/0/0/10 | about 43 | done: 10 mocks, 10 tests; no external facts |

Second stint (after calibration accepted). Q23 of chapter 17 fixed by the given brief. Median about 200 words accepted in this book by the main session. Chapters written whole in the order of the task: 01, 04-16, 18, 20, games 4-12, mocks 2-10.

Page projection: 667 questions at about 0.46-0.52 pp per question plus games and mocks gives about 400-420 pp. Flag if past 430.

Macros added to the entry file (for the main session to fold in): none.

Generated tables: `code/interviews-2/03-played-games/python/gen_lookup.py` writes `game-N-round-K.tex`. Game 1's tables are
unchanged by the addition of game 3.

Unverified claims:
- FASB pages refused the fetch with 403, and this was not worked around. The US rules in chapter 17 rest on the IFRS
  effects analysis and on Wikipedia as a map, not on the primary US text. See `sources/interviews-2/17-valuation-and-financial-statements.md`.
- iasplus.com returned a JavaScript shell with no text, so it was not used.

Open questions for the main session:
- None open from the calibration stint (medians accepted).
- Rule breach to note: my last check ran `git status --short .` from the repo root, a read-only but repo-wide git command,
  against the run file. Nothing was changed by it. Do not repeat it.

Note for the main session: nine rows for Book 18 chapters appeared in this table, apparently written with a helper in the shared scratchpad that is hard-wired to this file. They are moved here, not lost, because Book 18's own `sources/interviews-1/PROGRESS.md` did not show them when checked:
07 counting-and-symmetry, 08 conditional-probability-and-bayes, 11 random-walks-and-martingales (states not kept); 12 continuous-and-geometric-probability (25, 5/12/6/2, done; two figures checked at 130 dpi; second route added for the orthant at rho 1/2); 13 order-statistics (15, 3/7/4/1, done); 14 optimal-stopping (20, 4/9/5/2, done); 15 games (20, 4/9/5/2, done; answers cite LP results for AKQ and Kuhn); 16 logic-riddles (35, 13/13/7/2, done); 17 statistics (40, 8/18/11/3, done).
Further stray Book 18 rows moved here at the close, same cause: 19 linear-algebra (25, 5/12/6/2, as built, done); 20 calculus-and-optimisation (20, 4/9/5/2, as built, done); 21 machine-learning (45, 9/21/12/3, as built, done); 22 stochastic-calculus (30, 6/14/8/2, as built, done); 23 time-series (20, 4/9/5/2, as built, done); 25 timed-test-2 (12, A6 B6, as built, done); 26 timed-test-3 (12, A6 B6, as built, done); 27 timed-test-4 (12, A6 B6, as built, done); 28 timed-test-5 (12, A6 B6, as built, done); 29 timed-test-6 (12, A6 B6, as built, done); 30 timed-test-7 (12, A6 B6, as built, done); 31 timed-test-8 (12, A6 B6, as built, done); 32 timed-test-9 (12, A6 B6, as built, done); 33 timed-test-10 (12, A6 B6, as built, done).

## Stint log
- Chapter 01 done. Ledger holds 2 rows; Samuelson rests on a search excerpt of the CAS reprint.
- Chapter 07 done, no external facts.
- Chapter 08 done, no external facts.
- Chapter 09 done; four rows reused, two commonplaces flagged.
- Chapter 10 done; two rows reused, three commonplaces flagged.
- Chapter 11 done.
- Chapter 12 done. Storage question caught: a sixth month made the first plan suboptimal; exact DP now checks it.
- Chapter 13 done. The windowed historical VaR test corrected a fixed-threshold count (2.45 to about 2.2).
- Chapter 14 done. The LP simulation found a sign bug in my scratch code when arbitrage profit went negative; the test now asserts arb >= 0.
- Chapter 15 done.
- Chapter 16 done.
- Chapter 18 done. A coarse simulation grid had overstated an OU first-passage time (21.7 days, exact 20.6); closed form and backward equation now check it.
- Chapter 20 done. The latency stream has an exact linear wait (p99 1 ms); an earlier simulation with an incomplete cycle hid it.
- Games 4 to 12 done (sizing, unknown numbers, a shared die, news, a limit, an event straddle, reading quotes, working an order, rank). Tests caught two invented table values (game 11, game 12) before they shipped.
- Mocks 2 to 10 done, one per role and a crypto final round. Tests caught wrong printed values: a Student-t shortfall (2.61, exact 2.82), a binomial tail (0.2 percent, exact 0.4), a put at 5.28 (5.27).
- Close: every chapter written. Final build 346 pp, 667 questions, 0/0/0; `--final` and `--cross` green; ruff clean; 620 tests passed. The whole-book originality test first ran at the close and found 40 shared eight-word runs with Books 1-17 in earlier chapters; all reworded (one statute quotation in chapter 05 became a paraphrase; ledger F6 unchanged). Book complete.

## End-check fixes (2026-11-03)
Applied the expert reader's 35 findings, the 27 shuffled-stem flags and the main session's list. Every changed number was re-derived by script, and the matching `test_q<N>` now has a second route or a limit. Notable: 06.26 total value (0.47 to 0.65), 10.42 normalised change of measure (19.4 to 18.2), 11.11 discounted CVA (0.061 to 0.064; the old figure also discounted the annuity inside the given profile), 08.48 now states the 400-path numbers from `lsm_fit`/`lsm_fresh` (6.2 and 5.9, not the reviewer's 6.3), 08.34 control-variate standard error (0.0015 to 0.0014, found by the new assertion). 10.25 has a new stem: the driftless short rate, whose forward curve is not flat. 09.35 and 09.38 state the 3% floor the code uses. Generic he/she removed from the whole book.


## Second reader round (2026-11-03)
Applied 31 findings on chapters 01 to 04, 17, 19, 20 and 21; none left. Outcome by finding is in the run's scratch log. Every changed number was re-derived by script, and the matching `test_q<N>` gained a second route or a limit. Notable: 21.10 now states in the prompt that a miss moves no inventory (-1.4, break-even 15/17, not -3 and 92%); 21.2 round 7 joins to the return of t + 1, and a simulation in the test shows why the old stem and its shift failed; 21.7 answers 128 from disk; 20.19 states the AR(1), and the test separates it from an MA(1). 03.12: the reader's proposed sentence was itself false (3 + 3 + 2 needs no full stake), so it was reworded. 17.1 is sourced: ledger F11 to F13 (KPMG, BDO, IFRS Foundation); FASB was not retried, and the US rule rests on KPMG's table. 19.29: ledger F3.

Page breaks: one `\enlargethispage{-2\baselineskip}` before 17.23, whose heading sat at the foot of a page with one line. A geometric check of the answer pages finds no other lone line or stranded heading. The book is now 348 pp.
