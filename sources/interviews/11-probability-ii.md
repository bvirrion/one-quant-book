# 11. Probability II — brief and source ledger

## Brief

- **Hook.** 'You roll a die until two sixes in a row. How many rolls on average?' The candidate who writes two states on the whiteboard (no six yet; one six) and one equation for each has the answer, 42, in two minutes; the one who starts summing over sequences is still at it when the interviewer moves on.
- **Sections.** Expectation tricks: indicators and linearity; Recursions on states: first-step equations; Martingales and stopping: fair games, gambler's ruin and Wald's identity; Continuous problems: order statistics, the exponential clock and coupling.
- **Defines.** indicator decomposition, coupling argument.
- **Uses (defined earlier).** conditional expectation (B4.1), martingale (B4.1), stopping time (B4.1), Markov chain (B4.8), first-step analysis (B4.8), absorbing state (B4.8), hitting probability (B4.8), Poisson process (B4.6), Brownian motion (B4.2), optimal stopping problem (B4.10), symmetry argument (ch10), complementary counting (ch10).
- **Question bank.** 14 questions, 5/5/4. Families: expected counts by indicators (fixed points, runs, records, distinct values); waiting times for patterns (first-step equations, the two-patterns race); gambler's ruin with drift and its martingale solution; Wald's identity for a random number of trades; optimal stopping (a die game with one re-roll, the best-of-n selling rule); order statistics of uniforms (the expected spacing, the expected range); the exponential clock race (which order fills first); a coupling proof of a monotonicity claim. Roles: trader 5, researcher 6, risk 2, bank 1, mle 1. Firms: market maker 5, proprietary firm 2, systematic fund 3, bank 1, any 4.
- **Facts to verify.** origins: gambler's ruin (Pascal and Fermat, via Huygens 1657), Wald's identity (Wald 1944), Penney's game (Penney 1969), the secretary problem (Ferguson 1989 history) -- bibliographic.
- **Data.** Figures: one schematic (a state diagram of a pattern-waiting chain). Code: iv_prob2.py (first-step linear systems solved exactly with Fraction or sympy; closed forms checked by simulation over many seeds; order-statistic results by sympy integration).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Penney's game: Walter Penney, Journal of Recreational Mathematics, October 1969, p. 241 | Wikipedia, Penney's game (raw text, reference list) | https://en.wikipedia.org/w/index.php?title=Penney%27s_game&action=raw | 2026-09-29 | "Walter Penney, Journal of Recreational Mathematics, October 1969, p. 241" | section 2; omsources |
| F2 | Wald, On cumulative sums of random variables, Annals of Mathematical Statistics 15(3), 283-296, 1944 | Crossref | https://api.crossref.org/works/10.1214/aoms/1177731235 | 2026-09-29 | title, journal, volume, issue, pages | prop. Wald; omsources |
| F3 | Lindvall, Lectures on the Coupling Method, Wiley, 1992 | Open Library catalogue | https://openlibrary.org/works/OL4285482W | 2026-09-29 | title, author, first publication 1992 | omsources |

## EXCLUDED

