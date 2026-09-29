# 12. Brainteasers and Logic — brief and source ledger

## Brief

- **Hook.** A candidate is asked how a hundred people in a line, each seeing the hats in front, can agree a rule so that all but one name their own hat's colour. He says 'this is the parity puzzle' and recites a rule for two colours. The interviewer changes it to three colours and waits. The family was the point, not the puzzle.
- **Sections.** Invariants and parity; Working backwards: backward induction and games; Strategy stealing, pigeonholes and extremal arguments; Information puzzles: weighings, questions and common knowledge.
- **Defines.** invariant method, backward induction, strategy-stealing argument.
- **Uses (defined earlier).** Nash equilibrium (B4.29), entropy (B4.29), zero-sum game (B4.29), symmetry argument (ch10), indicator decomposition (ch11), sanity check (ch5).
- **Question bank.** 14 questions, 5/5/4. Families, each as a variant with its own answer: invariants (a board or token game whose reachable states a parity or sum modulo n decides; the hat line with k colours); backward induction (a division game among ranked players, an ultimatum sequence, a last-to-take game); strategy stealing (a first-player-wins proof); pigeonhole and extremal arguments; weighings and information (the number of weighings as a logarithm of the outcomes; a twelve-coin variant with a different count); common knowledge (an announcement puzzle with its own day count); a rope-timing or measuring puzzle variant. Roles: trader 7, researcher 4, developer 3, mle 1. Firms: market maker 6, proprietary firm 4, any 5.
- **Facts to verify.** origins: the hat puzzles (Ebert 1998 thesis; the Aspnes, Beigel, Furst and Rudich line), the pirate game (Stewart 1999, Scientific American), the twelve-coin problem (Grossman 1945 in the Scripta Mathematica or its documented first appearance), the muddy children and common knowledge (Littlewood 1953; Barwise 1981; Fagin, Halpern, Moses and Vardi 1995), strategy stealing (Nash's Hex argument, Gale 1979) -- bibliographic.
- **Data.** Figures: one schematic (a game tree solved by backward induction). Code: iv_teasers.py (every answer by exhaustive search: reachable states under the invariant, the backward-induction solution, the weighing strategy verified over all cases, the announcement puzzle simulated in a Kripke-model checker); exact tests.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Stewart, A puzzle for pirates, Scientific American 280(5), 98-99, 1999 | Crossref | https://api.crossref.org/works/10.1038/scientificamerican0599-98 | 2026-09-29 | title, journal, volume, issue, pages | section 2; omsources |
| F2 | Gale, A curious Nim-type game, American Mathematical Monthly 81(8), 876-879, 1974 | Crossref | https://api.crossref.org/works/10.1080/00029890.1974.11993683 | 2026-09-29 | title, journal, volume, issue, pages | section 3; omsources |
| F3 | Gale, The game of Hex and the Brouwer fixed-point theorem, American Mathematical Monthly 86(10), 818-827, 1979 | Crossref | https://api.crossref.org/works/10.1080/00029890.1979.11994922 | 2026-09-29 | title, journal, volume, issue, pages | section 3; omsources |
| F4 | Fagin, Halpern, Moses and Vardi, Reasoning about Knowledge, MIT Press (1995; paperback 2003); muddy children as the most frequent induction puzzle in epistemic logic | Wikipedia, Induction puzzles and Common knowledge (logic) (raw text, reference lists) | https://en.wikipedia.org/w/index.php?title=Common_knowledge_%28logic%29&action=raw | 2026-09-29 | "See the textbooks Reasoning about knowledge by Fagin, Halpern, Moses and Vardi (1995)" | section 4; omsources |
| F5 | Todd Ebert's 1998 PhD thesis at UC Santa Barbara publicised the simultaneous hat game; Hamming-code solution; reported in Winkler, Mathematical Puzzles: A Connoisseur's Collection | Wikipedia, Induction puzzles (raw text, citing Winkler) | https://en.wikipedia.org/w/index.php?title=Induction_puzzles&action=raw | 2026-09-29 | "One variation received some new publicity as a result of Todd Ebert's 1998 Ph.D. thesis at the University of California, Santa Barbara" | section 4; omsources |

## EXCLUDED

- Twelve-coin problem origin (Grossman 1945): not cited; the chapter's weighing question is the digital-scale variant.
- Winkler's book publisher and year (A K Peters, 2004) taken from the Wikipedia citation template; not independently verified.

