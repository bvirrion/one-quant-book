# 28. Hedging a Structured-Products Book — brief and source ledger

## Brief

- **Hook.** Retail investors buy autocallables in large size; the banks that sell them end up long volatility they must sell, short correlation and long dividends, and their hedging moves those markets.
- **Sections.** The autocallable book's exposures; Vega and skew; Correlation and dividends; Recycling trades.
- **Defines.** recycling trade, exotic book exposure.
- **Uses (defined earlier).** autocallable (B5.18), autocall trigger (B5.18), vega bucket (B5.26), structured product (B5.19), correlation skew (B5.17), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** vega recycling to hedge funds; dividend recycling; correlation recycling; skew hedge programme.
- **Tutorial.** Build a book of autocallables on firm.autocall, compute its vega, skew, dividend and correlation exposures, and simulate the recycling trades it offers and their price impact on the synthetic volatility market.
- **Build.** `firm.sphedge`: exposure aggregation for an autocallable book, recycling trade construction and a market-impact model of the hedging; Python.
- **Weekend problem.** Long what nobody wants — named result: the book's net exposures and the implied-volatility move its recycling causes.
- **Facts to verify.** Bank of Korea or Korean autocallable market reports (dated); Bouzoubaa and Osseiran 2010 exotic options and hybrids (Wiley).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | BIS Quarterly Review, September 2026, "Yields climb, yet risk appetite holds firm", Box B "Short on memory? Leveraged ETFs and chip stock volatility" (K. Todorov): autocallable structured products are widely sold to retail investors in Korea; they redeem early with an enhanced coupon above a barrier and expose holders to losses below a lower one; hedging them can require large, destabilising trades near the barriers; issuance referencing Samsung and SK Hynix rose sharply in the first half of 2026; the two stocks together exceed half the KOSPI 200 | BIS PDF, pdftotext | https://www.bis.org/publications/yields-climb-yet-risk-appetite-holds-firm.pdf | 2026-09-25 | "Hedging these products can require large, destabilising trades near the barriers. Issuance referencing Samsung and SK Hynix rose sharply in the first half of 2026" | hook; dat:s2:hedging-a-structured-products-book:korea; section 1; exercise 6; solutions; omsources |
| F2 | Eurex, "Dividend Derivatives" factsheet: dividend derivatives allow investors to take positions in, or hedge, future dividend payments "particularly for structured products and equity options" (as in chapter 26) | Eurex PDF, pdftotext | https://www.eurex.com/resource/blob/2687950/5c1a03353630cf01a86516868d888780/data/factsheet-dividend-derivatives.pdf | 2026-09-25 | "Dividend Derivatives allow investors to take positions in, or hedge, future dividend payments particularly for structured products and equity options." | section 3; strat:s2:hedging-a-structured-products-book:dividends |

## EXCLUDED

- Bank of Korea or Korean regulators' autocallable (ELS) statistics: not fetched; the BIS box is the public source used.
- Bouzoubaa and Osseiran 2010 (Exotic options and hybrids, Wiley): book, not fetched; not cited.
- Volumes of vega, dividend and correlation recycled by issuers, and the depth of the markets absorbing them: not public; the book (EUR 1 billion), its terms and the market depths (EUR 5, 10 and 20 million of vega per vol point) are planted.
- Named issuers' structured-products losses or recycling: no citable primary source; no firm named.
