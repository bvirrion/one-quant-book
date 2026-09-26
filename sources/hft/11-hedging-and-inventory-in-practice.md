# 11. Hedging and Inventory in Practice — brief and source ledger

## Brief

- **Hook.** At ten to four a stock market maker is long a basket of forty names it never chose; it can sell them, sell the index future against them, or keep them overnight and start tomorrow long.
- **Sections.** Choosing the hedge instrument; Partial hedging and hedge triggers; Inventory across correlated books; End of day and overnight.
- **Defines.** hedge instrument, delta-equivalent inventory, end-of-day flattening.
- **Uses (defined earlier).** hedging band (B5.26), internalisation (B1.10), cross-asset hedge ratio (B9.9), impulse control (B4.10), no-trade region (B4.10), closing price (B1.13), multi-asset market making (ch4), market maker (B1.1), bid--ask spread (B1.1), adverse selection (B1.1), mid price (B1.1), inventory (B2.30).
- **Tutorial.** On a simulated day of fills across forty names (firm.mmharness on firm_tape paths with a common factor), hedge with the future, with single stocks, or not at all, under band and trigger rules; compare hedging cost, residual risk and overnight gap exposure.
- **Build.** `firm.mmhedge`: delta-equivalent inventory across instruments by factor loadings, hedge-instrument choice by cost and residual risk, band and trigger policies on firm.impulse, end-of-day flattening schedules; Python.
- **Weekend problem.** Forty names at ten to four — named result: the cost and residual risk of the three hedging choices, and the overnight loss distribution of keeping the book.
- **Facts to verify.** Hendershott and Menkveld 2014 Price pressures (JFE); Menkveld 2013 inventory mean reversion of a high-frequency market maker (JFM); Comerton-Forde, Hendershott, Jones, Moulton, Seasholes 2010 Time variation in liquidity: the role of market-maker inventories and revenues (JF).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Hendershott and Menkveld (2014): NYSE intermediary data 1994-2005, 697 stocks; price pressure 0.49% (49 bp) on average with a half life of 0.92 days; largest-stock quintile 17 bp and 0.54 days; smallest quintile 118 bp and 2.11 days | T. Hendershott, A. J. Menkveld, "Price pressures", Journal of Financial Economics 114(3), 2014, 405-423 | https://ideas.repec.org/a/eee/jfinec/v114y2014i3p405-423.html ; authors' PDF http://faculty.haas.berkeley.edu/hender/price_pressures.pdf | 2026-09-25 | abstract: "0.49% on average with a half life of 0.92 days"; PDF p. 2: "Price pressure for the quintile of largest stocks is 17 basis points with a half life of 0.54 days. For the smallest stocks quintile, it is 118 basis points with a half life of 2.11 days" | §3 |
| F2 | Comerton-Forde, Hendershott, Jones, Moulton, Seasholes (2010): 11 years of NYSE specialist inventories and revenues; market-level and firm-level spreads widen when specialists have large positions or lose money; effects nonlinear, strongest when inventories are big or results poor | Journal of Finance 65(1), 2010, 295-331 | http://faculty.haas.berkeley.edu/hender/mm-inv-rev-liq.pdf | 2026-09-25 | abstract (pdftotext): "aggregate market-level and specialist firm-level spreads widen when specialists have large positions or lose money. The effects are nonlinear and most prominent when inventories are big or trading results have been particularly poor" | §3 |
| F3 | Menkveld (2013): the HFT market maker earns EUR 1.55 a trade on the spread net of fees and loses EUR 0.68 on positioning (gross EUR 0.88) | Journal of Financial Markets 16(4), 2013, 712-740 | https://doi.org/10.1016/j.finmar.2013.06.006 | 2026-09-25 | abstract: "The gross profit per trade is €0.88 which is the result of a €1.55 profit on the spread net of fees and a €0.68 'positioning' loss" (as in chapter 1, F5) | §3 |

## EXCLUDED

- The simulated day uses a fill model (firm.mmhedge.FlowDay), not forty firm_tape books: the machine limits of 2026-09-25 (one core, 1.5 GB) rule out forty full order-book simulations per day and per rule.
