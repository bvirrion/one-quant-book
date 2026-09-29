# 13. Betting and Market-Making Games — brief and source ledger

## Brief

- **Hook.** 'Make me a market on the sum of three dice.' The candidate says 8 at 10. The interviewer buys. 'Again.' 8 at 10. Buys again. 'Again.' The fair value is 10.5 and she has sold twice below it, to a counterparty who knows nothing more than she does and kept buying for exactly one reason. Everything in this chapter is about what the second 'again' should have told her.
- **Sections.** Pricing a bet: fair value, edge and the odds; Sizing: Kelly, fractions of Kelly and ruin; Making a market on an unknown: width, centre and what a trade tells you; Games with an informed counterparty, and when not to trade.
- **Defines.** none (the chapter uses the vocabulary of Books 1-17, listed below).
- **Uses (defined earlier).** odds (B2.29), edge (B2.29), Kelly criterion (B2.29), fractional Kelly (B2.29), risk of ruin (B2.29), make-me-a-market (B2.30), width (B2.30), inventory (B2.30), Bayesian update (B2.30), winner's curse (B2.30), adverse selection (B1.1), bid--ask spread (B1.1), mid price (B1.1), Nash equilibrium (B4.29), common-value auction (B4.29), bid shading (B4.29), Brier score (B16.26), trading game (ch6), Fermi estimate (ch9), calibrated interval (ch9).
- **Question bank.** 14 questions, 5/5/4. Families: fair value of a bet with a stake and a payout; a series of bets and the optimal fraction (Kelly with two outcomes, with three); the ruin probability of full against half Kelly (numeric); making a market on a dice sum, a card count and an estimation quantity, and updating after trades; the informed counterparty (what width breaks even against a given informed share); a sealed-bid game with a common value (the winner's curse, numeric shading); a betting game with a choice to stop. Roles: trader 9, researcher 3, risk 1, mle 1. Firms: market maker 7, proprietary firm 4, crypto firm 1, any 2.
- **Facts to verify.** none external beyond the method sources: Kelly 1956 (Bell System Technical Journal), Thorp 1969/2006, Glosten and Milgrom 1985 (pointers to Book 2 ch. 29-30 ledgers).
- **Data.** Figures: one chart (the market maker's expected profit against width for three informed shares, from the chapter's game; fig_iv_width.py). Code: iv_bets.py (exact dice and card distributions; Kelly fractions by exact optimisation with sympy; ruin probabilities exact for the lattice walk and by simulation; the informed-trader game simulated over many seeds, full size reference-marked).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Kelly, A new interpretation of information rate, Bell System Technical Journal 35(4), 917-926, 1956 | Crossref (pointer: ledger interviews/06 F3) | https://api.crossref.org/works/10.1002/j.1538-7305.1956.tb03809.x | 2026-09-29 | title, journal, volume, issue, pages | omsources |
| F2 | Glosten and Milgrom, Bid, ask and transaction prices in a specialist market with heterogeneously informed traders, JFE 14(1), 71-100, 1985 | Crossref | https://api.crossref.org/works/10.1016/0304-405X(85)90044-3 | 2026-09-29 | title, journal, volume, issue, pages | section 4; omsources |

## EXCLUDED

