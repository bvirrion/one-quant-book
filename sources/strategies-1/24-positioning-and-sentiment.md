# 24. Positioning and Sentiment — brief and source ledger

## Brief

- **Hook.** When speculators are at record long positions in a commodity, the next quarter's return is lower on average; the report that shows it is public every Friday.
- **Sections.** Positioning reports; Surveys and sentiment indices; Options positioning.
- **Defines.** positioning signal, sentiment index, hedging pressure.
- **Uses (defined earlier).** Commitments of Traders report (B3.9), managed money (B3.9), put--call ratio (ch15), backtest (B7.16), vectorised backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28), fundamental factor model (B7.24).
- **Strategy files.** hedging-pressure signal; extreme-positioning contrarian; options-positioning signal.
- **Tutorial.** Measure the CFTC corn positioning series from Book 3 as a signal for futures returns, simulate hedging pressure in firm.synthfut, and test contrarian positioning rules with Book 7's tools.
- **Build.** `firm.posisig`: positioning and sentiment signals from COT data (on firm.cot) and synthetic positioning, with publication lags; Python.
- **Weekend problem.** Record long — named result: the IC of the positioning signal and the effect of the Tuesday-to-Friday publication lag.
- **Facts to verify.** de Roon, Nijman, Veld 2000 hedging pressure (JF); Bessembinder 1992 (RFS); CFTC COT explanatory notes (dated); Baker and Wurgler 2006 investor sentiment (JF).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | CFTC Commitments of Traders: the report is generally published each Friday at 3:30 pm Eastern Time using data from the immediately preceding Tuesday; processing takes three days; holidays can change the schedule (a release schedule is published) | CFTC Commitments of Traders page | https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm | 2026-09-25 | "The COT Report is generally published each Friday at 3:30 pm Eastern Time (US), using the data from the immediately preceding Tuesday of that week" | hook; dat:s1:positioning-and-sentiment:cot; section 1 |
| F2 | F. A. de Roon, T. E. Nijman, C. Veld, "Hedging pressure effects in futures markets", Journal of Finance 55(3) (2000) 1437-1456: futures risk premia depend on own-market and cross-market hedging pressures; in 20 futures markets (financial, agricultural, mineral, currency), after controlling for systematic risk, own and within-group cross hedging pressure significantly affect futures returns, also after controlling for price pressure | Crossref metadata; OpenAlex abstract | https://doi.org/10.1111/0022-1082.00253 | 2026-09-25 | abstract: "both the futures own hedging pressure and cross-hedging pressures from within the group significantly affect futures returns" | section 1; strat:s1:positioning-and-sentiment:hedging; omsources |
| F3 | H. Bessembinder, "Systematic risk, hedging pressure, and risk premiums in futures markets", Review of Financial Studies 5(4) (1992) 637-667: returns in foreign currency and agricultural futures vary with the net holdings of hedgers after controlling for systematic risk, supporting hedging pressure as a determinant of futures premiums | Crossref metadata; OpenAlex abstract | https://doi.org/10.1093/rfs/5.4.637 | 2026-09-25 | abstract: "Returns in foreign currency and agricultural futures vary with the net holdings of hedgers, after controlling for systematic risk" | section 1; strat:s1:positioning-and-sentiment:hedging; omsources |
| F4 | M. Baker, J. Wurgler, "Investor sentiment and the cross-section of stock returns", Journal of Finance 61(4) (2006) 1645-1680: when beginning-of-period sentiment proxies are low, subsequent returns are relatively high for small, young, high-volatility, unprofitable, non-dividend-paying, extreme-growth and distressed stocks; when sentiment is high these categories earn relatively low subsequent returns | Crossref metadata; OpenAlex abstract; NBER w10449 | https://doi.org/10.1111/j.1540-6261.2006.00885.x ; https://www.nber.org/papers/w10449 | 2026-09-25 | abstract: "when beginning-of-period proxies for sentiment are low, subsequent returns are relatively high for small stocks, young stocks, high volatility stocks, unprofitable stocks" | section 2; strat:s1:positioning-and-sentiment:options; omsources |
| F5 | CBOT corn disaggregated Commitments of Traders, futures only, weekly (Tuesday), 5 Jan 2016 to 15 Sep 2026 (data/markets-3/cot_corn_disagg.csv) | CFTC historical compressed files | https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm | 2026-09-24 | data file and its LICENSES.md row (US government data, public) | section 1; strat:s1:positioning-and-sentiment:extreme |
| F6 | IMF global price of maize, $/tonne, monthly, Jan 2000 to Jul 2026 (data/markets-3/ags_monthly.csv) | FRED series PMAIZMTUSDM (IMF Primary Commodity Prices) | https://fred.stlouisfed.org/series/PMAIZMTUSDM | 2026-09-24 | data file and its LICENSES.md row (IMF terms, with attribution) | section 1 |

## EXCLUDED

- The hook's claim that record speculative longs in a commodity are followed by lower returns: no source fetched, and the chapter's own corn data (2017-2026) point the other way; the hook was rewritten around the COT schedule.
- Options positioning studies beyond chapter 15's sources: none fetched; the options-positioning file points to chapter 15.
- The synthetic hedging pressure, its premium and the speculators' trend-chasing are the chapter's own choices.
