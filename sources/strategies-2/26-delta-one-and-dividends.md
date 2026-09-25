# 26. Delta-One and Dividends — brief and source ledger

## Brief

- **Hook.** A bank that sells autocallables is left long dividends it did not want; it sells them in dividend futures and swaps, and the dividend market is priced by that supply.
- **Sections.** Index arbitrage at a bank; Financing trades; Dividend risk from structured issuance; Dividend trades.
- **Defines.** index arbitrage, financing trade, dividend supply pressure.
- **Uses (defined earlier).** delta-one (B1.17), dividend future (B1.22), dividend risk (B5.5), fair value (B1.21), autocallable (B5.18), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** index arbitrage; total-return swap financing; long dividends against structured supply; dividend calendar spread.
- **Tutorial.** Simulate index futures and their fair value with planted financing spreads, run index arbitrage, and model dividend futures priced below expected dividends because structured-product hedgers sell them.
- **Build.** `firm.deltaone`: index fair value, arbitrage bands, financing trades and a dividend market with structured supply; Python.
- **Weekend problem.** Dividends nobody wanted — named result: the dividend trade's return from the supply discount.
- **Facts to verify.** Binsbergen, Brandt, Koijen 2012 on the timing and pricing of dividends (AER); Eurex dividend futures (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | J. van Binsbergen, M. Brandt, R. Koijen, "On the timing and pricing of dividends", American Economic Review 102(4) (2012) 1596-1618: prices of dividend strips (short-term assets paying the index's dividends up to T) recovered; expected returns, Sharpe ratios and volatilities of short-term assets higher than the index's, CAPM betas below one; short-term assets more volatile than their realisations; inconsistent with many leading theories | Crossref metadata; OpenAlex abstract | https://doi.org/10.1257/aer.102.4.1596 | 2026-09-25 | abstract: "expected returns, Sharpe ratios, and volatilities on short-term assets are higher than on the index, while their CAPM betas are below one" | hook; section 4; strat:s2:delta-one-and-dividends:dividends; exercise 5; solutions; omsources |
| F2 | R. Manley, C. Mueller-Glissmann, "The market for dividends and related investment strategies", Financial Analysts Journal 64(3) (2008) 17-29: a market for index and single-stock dividends has developed, like the Treasury strip market; since 2004 dividend swaps have been a major profit contributor for multistrategy and macro hedge funds because market-implied dividends traded at high discounts and dividend growth was strong | Crossref metadata; OpenAlex abstract | https://doi.org/10.2469/faj.v64.n3.4 | 2026-09-25 | abstract: "dividend swaps have been a major profit contributor for multistrategy and macro hedge funds because market-implied dividends have been trading at high discounts and dividend growth has been strong" | section 3; strat:s2:delta-one-and-dividends:dividends; solutions; omsources |
| F3 | J. Kragt, F. de Jong, J. Driessen, "The dividend term structure", Journal of Financial and Quantitative Analysis 55(3) (2020; online 2019) 829-867: a two-factor model (mean reversion within a year and at the business-cycle horizon) fits EURO STOXX 50 dividend futures prices; investors update the valuation of dividends beyond the business cycle only to a limited degree; the factors explain much of daily stock returns | Crossref metadata; OpenAlex abstract | https://doi.org/10.1017/S002210901900036X | 2026-09-25 | abstract: "A 2-factor model capturing short-term mean reversion within a year and a medium-term component reverting at the business-cycle horizon gives an excellent fit of these prices" | section 4; strat:s2:delta-one-and-dividends:calendar; solutions; omsources |
| F4 | Eurex, "Dividend Derivatives" factsheet: EURO STOXX 50 Index Dividend Futures (FEXD) on the EURO STOXX 50 DVP index, EUR 100 per index dividend point, expiries over 10 years (4 semi-annual June/December then 8 annual December), cash settled, last trading day the third Friday of the expiry month; dividend derivatives let investors take positions in or hedge future dividend payments "particularly for structured products and equity options" | Eurex PDF, pdftotext | https://www.eurex.com/resource/blob/2687950/5c1a03353630cf01a86516868d888780/data/factsheet-dividend-derivatives.pdf | 2026-09-25 | "Dividend Derivatives allow investors to take positions in, or hedge, future dividend payments particularly for structured products and equity options." | dat:s2:delta-one-and-dividends:fexd; section 3 |

## EXCLUDED

- Measured dividend futures discounts, structured-product issuance volumes and issuers' dividend positions: not fetched (licensed data); the supply discount (4% of expected dividends per year of maturity) is the chapter's planted assumption, and the link from autocallable issuance to issuers' long dividend exposure is computed with Book 5's pricer, not cited.
- Futures-implied financing spreads and quarter-end premia: the levels are planted (mean 20 bp, quarter-end 25 bp).
- Named banks' delta-one or dividend books: no citable primary source; no firm named.
