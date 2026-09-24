# 29. Thinking in Expected Value — brief and source ledger

## Brief

- **Hook.** In 2016, 61 quantitatively trained people were given 25 dollars and 30 minutes to bet on a coin that landed heads 60% of the time; 28% of them went bust.
- **Sections.** Edge and odds; The Kelly criterion; Fractional Kelly and risk of ruin; When the edge itself is uncertain.
- **Defines.** edge, odds, Kelly criterion, fractional Kelly, growth rate, risk of ruin, drawdown.
- **Uses (defined earlier).** leverage.
- **Tutorial.** Simulate repeated bets at several Kelly fractions and plot the distribution of terminal wealth.
- **Build.** `firm.sizing`: sizing module (Kelly, fractional, drawdown-constrained).
- **Weekend problem.** The uncertain edge — named result: the optimal Kelly fraction when the edge is estimated from 200 trades.
- **Facts to verify.** Kelly 1956 paper; Thorp; Haghani & Dewey 2016 coin-flip experiment.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Haghani and Dewey experiment: 61 subjects, groups of 2-15; USD 25 stake; coin biased to 60% heads; 30 minutes; maximum payout USD 250 (revealed if approached); 7,253 flips in aggregate; only 21% reached the maximum, against 95% expected with a constant 10-20% betting strategy; one third ended below their start; 28% went bust; average payout USD 91; average bet 15% of bankroll; 18 subjects bet everything on one flip; some bet on tails; Kelly fraction bet: expected gain 4% per flip; at 300 flips (one every 6 s) expected value USD 25 x 1.04^300 = USD 3,220,637; total winnings paid USD 5,574 | V. Haghani and R. Dewey, "Rational Decision-Making Under Uncertainty: Observed Betting Patterns on a Biased Coin", SSRN/arXiv, 19 October 2016 | https://arxiv.org/pdf/1701.01427 | 2026-09-24 | "More astounding still is the fact that 28% of participants went bust and received no payout." | hook; §1; §2; problem |
| F2 | Kelly (1956): J. L. Kelly Jr., "A New Interpretation of Information Rate", Bell System Technical Journal (as listed in Haghani and Dewey's references) | Haghani and Dewey (2016), reference list | https://arxiv.org/pdf/1701.01427 | 2026-09-24 | "Kelly, J.L., 1956. A new interpretation of information rate. Bell System Technical Journal" | §2; omsources |

## EXCLUDED

- Thorp's applications of Kelly (blackjack, Princeton-Newport): not fetched; not stated.
- The drawdown formula alpha^(2/c-1) and the shrinkage c* = n SR^2 / (n SR^2 + 1) are derived in the chapter and checked by simulation; no external source is needed.

