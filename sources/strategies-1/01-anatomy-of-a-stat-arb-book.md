# 1. Anatomy of a Stat-Arb Book — brief and source ledger

## Brief

- **Hook.** A book holds 1,800 stocks long and 1,800 short, each position under 0.2 per cent of capital; on its best day it makes 0.4 per cent and on its worst loses 0.6, and its annual profit is the sum of three million small bets.
- **Sections.** Thousands of small bets; Neutrality: dollar, beta, sector, factor; Financing: cash, leverage, borrow and rebates; What public descriptions of such books say; The daily cycle of a stat-arb book.
- **Defines.** statistical arbitrage, stat-arb book, hard-to-borrow list, daily P&L attribution.
- **Uses (defined earlier).** gross exposure (B1.7), net exposure (B1.7), short sale (B1.6), securities lending (B1.6), rebate rate (B1.6), borrow fee (B1.6), leverage (B1.6), general collateral (B1.16), dollar neutrality (B7.25), beta neutrality (B7.25), factor-neutrality constraint (B7.25), fundamental law of active management (B7.15), breadth (B7.15).
- **Tutorial.** Assemble a daily stat-arb book on firm.synthmkt from Book 7's reversal and momentum predictors: build it with firm.portcons, finance it (margin, borrow fees by name, rebates on short proceeds), run the daily cycle, and attribute each day's P&L to factors, specific returns, costs and financing.
- **Build.** `firm.statbook`: stat-arb book accounting (positions, cash, margin and leverage, borrow fees and short rebates by name, a hard-to-borrow list) with daily P&L attribution into factor, specific, cost and financing terms that adds up; Python.
- **Weekend problem.** Three million small bets — named result: the share of a year's stat-arb P&L explained by factor exposures a neutral book was not supposed to have, and the financing drag as a fraction of gross alpha.
- **Facts to verify.** Khandani and Lo 2011 (as B7.28); Avellaneda and Lee 2010, Statistical arbitrage in the US equities market (Quantitative Finance); Reg T initial margin 50 per cent (12 CFR 220, eCFR); FINRA Rule 4210 portfolio margin (dated); Pedersen 2015, Efficiently Inefficient (Princeton).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | M. Avellaneda, J.-H. Lee, "Statistical arbitrage in the US equities market", Quantitative Finance 10(7) (2010) 761-782: signals from PCA or regressions on sector ETFs, idiosyncratic returns modelled as mean-reverting; after transaction costs PCA strategies had an average annual Sharpe ratio of 1.44 over 1997-2007, stronger before 2003 and 0.9 in 2003-2007; ETF strategies 1.1 over 1997-2007 with a similar degradation since 2002; with volume information 1.51 in 2003-2007; detailed study of the summer 2007 liquidity crisis | Crossref metadata; OpenAlex record with abstract | https://doi.org/10.1080/14697680903124632 | 2026-09-25 | "After accounting for transaction costs, PCA-based strategies have an average annual Sharpe ratio of 1.44 over the period 1997 to 2007, with stronger performances prior to 2003. During 2003-2007, the average Sharpe ratio of PCA-based strategies was only 0.9" | section 4; iq 4; omsources |
| F2 | A. E. Khandani, A. W. Lo (2011): as Book 7 chapter 28, F1 | as Book 7 | https://doi.org/10.1016/j.finmar.2010.07.005 | 2026-09-25 | as Book 7 | section 4; omsources |
| F3 | L. H. Pedersen, Efficiently Inefficient: How Smart Money Invests and Market Prices Are Determined, Princeton University Press (2015) | Crossref metadata | https://doi.org/10.1515/9781400865734 | 2026-09-25 | Crossref: author, title, Princeton University Press, 2015 | section 4; omsources |
| F4 | Regulation T, 12 CFR 220.12: the required margin for a margin equity security is 50% of its current market value; for a short sale of a nonexempted security 150% of its current market value (100% where a convertible or exchangeable security is held) | eCFR API, title 12 part 220 section 220.12 | https://www.ecfr.gov/current/title-12/chapter-II/subchapter-A/part-220/section-220.12 | 2026-09-25 | "Margin equity security ... 50 percent of the current market value of the security"; "Short sale of a nonexempted security ... 150 percent of the current market value of the security" | dat:s1:anatomy-of-a-stat-arb-book:margin; section 3; exo 3 |
| F5 | FINRA Rule 4210: members may elect portfolio margin (paragraph (g)) as an alternative to strategy-based margin; the market move for an eligible product that is, or is based on, an equity security is +/- 15%; strategy-based maintenance for a short stock at $5 or above is $5 per share or 30% of market value, whichever is greater | FINRA rulebook page for Rule 4210 | https://www.finra.org/rules-guidance/rulebooks/finra-rules/4210 | 2026-09-25 | "As an alternative to the 'strategy-based' margin requirements set forth in paragraphs (a) through (f) of this Rule, members may elect to apply the portfolio margin requirements"; "Any other eligible product that is, or is based on, an equity security or a narrow-based index +/- 15%"; "$5.00 per share or 30 percent of the current market value, whichever amount is greater, of each stock 'short'" | dat:s1:anatomy-of-a-stat-arb-book:margin; section 3; exo 3 |

## EXCLUDED

- Named firms' stat-arb books (sizes, leverage, numbers of positions): no primary public source fetched; none named.
- Pedersen (2015), the book's content: only its metadata accessed; cited as further reading.
- Every number about the book (positions, returns, attribution, financing) is computed on firm.synthmkt and tested.

