# 8. Convertible Arbitrage — brief and source ledger

## Brief

- **Hook.** Buy the convertible, short the stock, and the trade is long volatility and credit, short the borrow; in 2005 and 2008 funds found out how much of each they owned at once.
- **Sections.** What a convertible holder owns; The hedged trade and its Greeks; Credit and borrow; 2005 and 2008.
- **Defines.** busted convertible, convertible delta hedge, credit-hedged convertible.
- **Uses (defined earlier).** convertible arbitrage (B5.21), convertible bond (B5.21), borrow fee (B1.6), credit default swap (B2.23), implied volatility (B1.25), realised volatility (B1.25), delta hedging (B1.26), vega (B5.4), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** delta-hedged convertible; credit-hedged convertible; busted convertible credit trade; new-issue convertible.
- **Tutorial.** Price convertibles on firm.synthvol stocks with a credit spread tied to the stock, hedge them in delta and credit, and run the book through a planted episode of redemptions, widening credit and recalled borrow.
- **Build.** `firm.convarb`: convertible book on firm.convertible's pricer with delta and credit hedges, borrow costs and a forced-selling scenario; Python.
- **Weekend problem.** Long everything at once — named result: the hedged book's carry and its loss in the planted forced-selling episode, and the share from credit.
- **Facts to verify.** Mitchell, Pedersen, Pulvino 2007 slow moving capital (AER P&P); Agarwal, Fung, Loon, Naik 2011 risk and return in convertible arbitrage (J. Empirical Finance).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | M. Mitchell, L. H. Pedersen, T. Pulvino, "Slow moving capital", American Economic Review 97(2) (2007) 215-220 (NBER w12877): convertible arbitrage funds account for up to 75% of the convertible market; convertibles are often issued below fundamental value and continue to trade below it; the primary risk is further cheapening and forced liquidation; in Q1 2005 more than 20% of capital was redeemed from convertible arbitrage funds (Barclay Group); 28 specialised funds sold 35% of their convertibles by end-2005; the median discount of market to theoretical value reached 2.7% in mid-May 2005, about 2.5 standard deviations from its 1985-2004 average, the largest since LTCM's liquidation in August 1998; convertible hedge funds returned -7.2% in January-May 2005, roughly a 2.7% cheapening at typical leverage of 3:1 | Crossref metadata; OpenAlex abstract; NBER working paper PDF (pdftotext) | https://doi.org/10.1257/aer.97.2.215 ; https://www.nber.org/system/files/working_papers/w12877/w12877.pdf | 2026-09-25 | "more than 20% of capital was redeemed from convertible arbitrage funds in the 1st quarter of 2005"; "reaching a maximum discount of 2.7% in mid-May 2005"; "convertible hedge funds had returns of -7.2% during January-May 2005"; "assuming a typical fund leverage of 3:1" | hook; section 1; section 4; strat:s2:convertible-arbitrage:newissue; omsources |
| F2 | M. Mitchell, T. Pulvino, "Arbitrage crashes and the speed of capital", Journal of Financial Economics 104(3) (2012) 469-490: the imminent failure of prime brokers in 2008 caused a sudden decrease in the leverage afforded hedge funds; seemingly long-term debt capital became short-term; arbitrageurs became unable to maintain similar prices of similar assets | Crossref metadata; RePEc abstract | https://doi.org/10.1016/j.jfineco.2011.09.002 | 2026-09-25 | "The imminent failure of prime brokers during the 2008 financial crisis caused a sudden decrease in the leverage afforded hedge funds" | section 4; omsources |
| F3 | V. Agarwal, W. H. Fung, Y. C. Loon, N. Y. Naik, "Risk and return in convertible arbitrage: evidence from the convertible bond market", Journal of Empirical Finance 18(2) (2011) 175-194: a buy-and-hedge strategy (long convertibles, hedging equity risk alone) explains much of convertible arbitrage funds' returns; extreme market-wide events and the supply of convertibles matter; larger funds short more stock and are more exposed to supply shocks; arbitrageurs are rewarded for funding issuers while passing part of the equity risk to the equity market | Crossref metadata; RePEc abstract | https://doi.org/10.1016/j.jempfin.2010.11.008 | 2026-09-25 | "the returns of a buy-and-hedge strategy involving taking a long position in convertible bonds ... while hedging the equity risk alone explains a substantial amount of these funds' return dynamics" | section 2; strat:s2:convertible-arbitrage:delta; omsources |

## EXCLUDED

- 2008 convertible discounts and fund returns (magnitudes): not in the fetched abstract of Mitchell and Pulvino (2012); the chapter states only the leverage mechanism.
- Named convertible arbitrage funds and their losses: none quoted (Amaranth appears in MPP's footnote but is not used).
- The synthetic cheapness path (3% at issue, 1% normal, 6% at the episode's depth), hazard doubling and borrow fee of 5% are the chapter's own choices.

