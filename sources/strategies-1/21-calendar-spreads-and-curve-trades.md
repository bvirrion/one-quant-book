# 21. Calendar Spreads and Curve Trades — brief and source ledger

## Brief

- **Hook.** The front-month WTI contract settled at minus thirty-seven dollars on 20 April 2020; the next month traded above twenty. A spread trade that looked safe for twenty years met a storage limit.
- **Sections.** Trading the shape of a futures curve; Mean reversion of spreads; Storage limits and the 2020 negative price; Curve trades in rates and volatility futures.
- **Defines.** curve trade, spread mean reversion, storage-limit risk.
- **Uses (defined earlier).** calendar spread (B1.19), contango (B1.21), backwardation (B1.21), convenience yield (B3.10), backtest (B7.16), vectorised backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28), fundamental factor model (B7.24).
- **Strategy files.** front-second spread mean reversion; curve steepener in commodity futures; roll-period calendar spread; volatility futures curve trade.
- **Tutorial.** Measure the WTI 1--2 spread's persistence in the EIA data, trade its mean reversion, and show what April 2020 did; build curve trades on firm.synthfut curves.
- **Build.** `firm.curvestrat`: spread construction from futures curves, mean-reversion signals with regime filters, and curve trades; Python.
- **Weekend problem.** Minus thirty-seven — named result: the spread strategy's Sharpe ratio before 2020 and its loss in April 2020.
- **Facts to verify.** EIA WTI futures c1-c4 (as B3); CFTC interim staff report on 20 April 2020 WTI (November 2020); Gorton, Hayashi, Rouwenhorst 2013 fundamentals of commodity futures returns (Review of Finance).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | CFTC Division of Market Oversight and Office of the Chief Economist, Interim Staff Report on Trading in NYMEX WTI Crude Oil Futures Contract Leading up to, on, and around April 20, 2020 (November 2020): the May 2020 contract settled at -$37.63 per barrel on April 20, the first negative price since the contract was listed 37 years earlier; prices fell from $17.73 at the start of the session; an oversupplied market met an unprecedented fall in demand from COVID-19; by March 2020 working storage at Cushing, Oklahoma (the delivery point) was near capacity | CFTC report (PDF, pdftotext) and press release 8315-20 | https://www.cftc.gov/media/5296/InterimStaffReportNYMEX_WTICrudeOil/download ; https://www.cftc.gov/PressRoom/PressReleases/8315-20 | 2026-09-25 | "settled on April 20 at a price of -$37.63 per barrel"; "the first time the WTI Contract traded at a negative price since being listed for trading 37 years ago"; "By March 2020, the working storage available at the Cushing facility was near capacity" | hook; section 3; strat:s1:calendar-spreads-and-curve-trades:front; omsources |
| F2 | G. B. Gorton, F. Hayashi, K. G. Rouwenhorst, "The fundamentals of commodity futures returns", Review of Finance 17(1) (2013, online 2012) 35-105: commodity futures risk premiums vary with physical inventories; the convenience yield is a decreasing, nonlinear function of inventories; the basis, prior returns and volatility reflect inventories and are informative about risk premiums; 31 commodities, 1971-2010; no evidence that futures positions predict premiums | Crossref metadata; OpenAlex abstract | https://doi.org/10.1093/rof/rfs019 | 2026-09-25 | abstract: "The convenience yield is a decreasing, nonlinear function of inventories"; "Price measures, such as the futures basis ... reflect the state of inventories and are informative about commodity futures risk premiums" | section 1; section 3; strat:s1:calendar-spreads-and-curve-trades:steepener; omsources |
| F3 | D. P. Simon, J. Campasano, "The VIX futures basis: evidence and trading strategies", Journal of Derivatives 21(3) (2014) 54-69: from 2006 to 2011 the VIX futures basis has no significant forecast power for the change in spot VIX but does for VIX futures price changes; shorting VIX futures in contango and buying them in backwardation, hedged with mini-S&P 500 futures, is highly profitable and robust to costs and out-of-sample hedge ratios | Crossref metadata; authors' 2013 EFMA version (pdftotext) | https://doi.org/10.3905/jod.2014.21.3.054 ; https://www.efmaefm.org/0efmameetings/efma%20annual%20meetings/2013-Reading/papers/VIX%20paper_EFMA.pdf | 2026-09-25 | abstract: "the VIX futures basis does not have significant forecast power for the change in the spot VIX from 2006 through 2011 but does have forecast power for VIX futures price changes" | section 4; strat:s1:calendar-spreads-and-curve-trades:vix; omsources |
| F4 | NYMEX WTI crude oil futures daily settlements, contracts 1 to 4 (EIA), 1985-2024, as in chapters 19-20 and Book 3 | US Energy Information Administration, series RCLC1D-RCLC4D | https://www.eia.gov/dnav/pet/hist/RCLC1D.htm | 2026-09-24 | data file and its LICENSES.md row (EIA: public domain) | sections 2-3; strat:s1:calendar-spreads-and-curve-trades:front; strat:s1:calendar-spreads-and-curve-trades:roll |

## EXCLUDED

- Exchange fees and the tick size of the listed WTI calendar spread: not fetched; the chapter's cost of one cent a barrel per unit traded is labelled an assumption.
- Rates curve trades (SOFR futures packs, bond futures spreads): described from Books 2 and 6; no performance figure verified.
- The OpenAlex abstract attached to the Simon-Campasano DOI belongs to another paper (a ChIP-seq toolkit): the authors' own version was used instead.
