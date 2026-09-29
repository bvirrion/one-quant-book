# 6. The Final Round and Trading Games — brief and source ledger

## Brief

- **Hook.** Six candidates sit around a table with chips and a deck of cards; the interviewer asks for a market on the sum of the next three cards. One quotes 17 at 23 and never moves it; one tightens after every trade and is picked off twice by the same player; one says 'I am lifting the offer because two high cards are gone.' The assessor behind them writes down three different things.
- **Sections.** The final round: its shape and who decides; Mock trading and betting games: what is scored; Group exercises and presentations; What assessors write down, and the debrief.
- **Defines.** final round, superday, trading game, group exercise.
- **Uses (defined earlier).** make-me-a-market (B2.30), width (B2.30), inventory (B2.30), Bayesian update (B2.30), winner's curse (B2.30), adverse selection (B1.1), bid--ask spread (B1.1), mid price (B1.1), odds (B2.29), edge (B2.29), Kelly criterion (B2.29), hiring committee (ch2), interview rubric (ch1), interview loop (ch1), think-aloud protocol (ch5).
- **Question bank.** 10 questions, 3/4/3. Families: a short trading game played in the bank (card-sum and dice markets with an informed counterparty; numeric fair values and the update after a trade); what the assessor scores in a game transcript; a betting game with a budget and a stopping choice (numeric, Kelly-flavoured); a group estimation exercise and the role to play; a presentation question under challenge. Roles: trader 6, researcher 2, risk 1, bank 1. Firms: market maker 5, proprietary firm 2, bank 1, any 2.
- **Facts to verify.** assessment-centre research: Arthur, Day, McNelly and Edens 2003 (Personnel Psychology) meta-analysis; International Taskforce on Assessment Center Guidelines 2015 (Journal of Management); published descriptions of final rounds and trading games by firms that describe them (dated; pointer to Book 2 ch. 30 ledger, 'the training games firms describe'); the use of the word 'superday' by banks' own careers pages (dated).
- **Data.** Figures: one chart (a card-sum market's fair value and a candidate's quotes over a played game, from a seeded simulation; fig_iv_game.py). Code: iv_game.py (exact card-sum distributions by enumeration, fair value after each reveal, the informed player's profit against quote rules), simulated over many seeds.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Arthur, Day, McNelly and Edens, A meta-analysis of the criterion-related validity of assessment center dimensions, Personnel Psychology 56(1), 125-153, 2003: 34 articles; 168 dimension labels collapsed into six (consideration/awareness of others, communication, drive, influencing others, organizing and planning, problem solving); estimated true validities .25 to .39 | Crossref (citation); OpenAlex (abstract) | https://api.crossref.org/works/10.1111/j.1744-6570.2003.tb00146.x | 2026-09-29 | "we collapsed 168 assessment center dimension labels into an overriding set of 6 dimensions"; "a range of estimated true criterion-related validities from .25 to .39" | section 3; omsources |
| F2 | International Task Force on Assessment Center Guidelines, Guidelines and ethical considerations for assessment center operations, International Journal of Selection and Assessment 17(3), 243-253, 2009 | Crossref | https://api.crossref.org/works/10.1111/j.1468-2389.2009.00467.x | 2026-09-29 | title, journal, volume, issue, pages | omsources |
| F3 | Kelly, A new interpretation of information rate, Bell System Technical Journal 35(4), 917-926, 1956 | Crossref | https://api.crossref.org/works/10.1002/j.1538-7305.1956.tb03809.x | 2026-09-29 | title, journal, volume, issue, pages | omsources |
| F4 | Banks' use of the word "Superday" for a final round of two to five interviews (Goldman Sachs) | pointer: ledger interviews/02 F1 | https://www.goldmansachs.com/careers/students/prepare | 2026-09-29 | "6. Superday ... a series of final round interviews" | def:iv:the-final-round-and-trading-games:final |

## EXCLUDED

- Firms' published descriptions of trading games: not restated; pointer to Book 2 ch. 30.

