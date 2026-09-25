# 23. Measuring Market Making and Execution — brief and source ledger

## Brief

- **Hook.** A market maker's year ends flat. Its books show spread capture of plus two million, adverse selection of minus one point seven, and inventory losses of minus three hundred thousand.
- **Sections.** Mark-out curves; Fill rates and hit ratios; The market maker's P&L, decomposed; Measuring execution; Transaction cost analysis.
- **Defines.** mark-out curve, spread capture, adverse-selection cost, inventory P\&L, fill rate, hit ratio, transaction cost analysis, delay cost, opportunity cost, VWAP slippage.
- **Uses (defined earlier).** mark-out (B2.15), adverse selection (B1.1), effective spread (B1.10), realised spread (B1.10), microprice (ch8), implementation shortfall (ch19), arrival price (ch19), volume-weighted average price (ch2), order-book replay (ch18), market impact (ch18).
- **Tutorial.** Run a simple market maker in firm.lobreplay, draw its mark-out curves by counterparty type, decompose its P&L into spread capture, adverse selection and inventory, and write the TCA report of a parent order.
- **Build.** `firm.markout`: mark-out curves (mid or microprice reference, horizons, groupings), fill and hit statistics, market-maker P&L decomposition that adds up exactly, implementation-shortfall decomposition and a TCA report; Python.
- **Weekend problem.** The flat year — named result: the decomposition of a simulated market maker's annual P&L into spread capture, adverse selection, inventory and fees, and the horizon at which its mark-outs settle.
- **Facts to verify.** Perold 1988 (JPM); Menkveld 2013, high frequency trading and the new market makers (J. Financial Markets); Kissell 2013, The Science of Algorithmic Trading and Portfolio Management; Hasbrouck 2007, Empirical Market Microstructure.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | A. J. Menkveld, "High Frequency Trading and the New-Market Makers", Tinbergen Institute Discussion Paper TI 11-076/2/DSF 21 (version of 15 Aug 2011; published in Journal of Financial Markets 16(4) (2013) 712-740): a large HFT acting as a modern market maker on Chi-X and Euronext trades on average 1,397 times per stock per day in Dutch index stocks; gross profit per trade EUR 0.88, the result of a EUR 1.55 profit on the spread net of fees and a EUR 0.68 positioning loss; the loss decomposes into a EUR 0.45 profit on positions of less than five seconds and a EUR 1.13 loss on longer positions; Sharpe ratio 9.35 on committed capital | Tinbergen Institute discussion paper PDF (abstract), pdftotext; Crossref metadata for the journal version | http://papers.tinbergen.nl/11076.pdf | 2026-09-25 | "The gross profit per trade is EUR 0.88 which is the result of a EUR 1.55 profit on the spread net of fees and a EUR 0.68 'positioning' loss. This loss decomposes into a EUR 0.45 profit on positions of less than five seconds, but a loss of EUR 1.13 on longer duration positions" | section 3; iq 3; omsources |
| F2 | J. Brogaard, T. Hendershott, R. Riordan, "High-Frequency Trading and Price Discovery", Review of Financial Studies 27(8) (2014): HFTs trade in the direction of permanent price changes through their liquidity-demanding orders; their liquidity-supplying orders are adversely selected; the direction of their trading predicts price changes over horizons of seconds and correlates with order-book imbalances | OpenAlex record with abstract | https://doi.org/10.1093/rfs/hhu032 | 2026-09-25 | "HFTs' liquidity supplying orders are adversely selected"; "The direction of HFTs' trading predicts price changes over short horizons measured in seconds"; "correlated with ... limit order book imbalances" | section 1; omsources |
| F3 | A. F. Perold (1988): as chapter 19, F1 (the term implementation shortfall) | as chapter 19 | https://doi.org/10.3905/jpm.1988.409150 | 2026-09-25 | as chapter 19 | section 4; omsources |

## EXCLUDED

- Kissell (2013/2014), The Science of Algorithmic Trading and Portfolio Management, and Hasbrouck (2007), Empirical
  Market Microstructure: only chapter metadata reachable (Crossref), not accessed; not cited.
- The decomposition of a market maker's P&L into spread capture, adverse selection to a horizon and inventory, and of
  implementation shortfall into delay, execution, opportunity and fees, is the chapter's own presentation; Menkveld's
  spread/positioning split is cited as the empirical precedent.
- Every mark-out, P&L component, fill rate and TCA number is computed on firm.tape and tested.

