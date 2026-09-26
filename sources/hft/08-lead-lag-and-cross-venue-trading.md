# 8. Lead--Lag and Cross-Venue Trading — brief and source ledger

## Brief

- **Hook.** When the index future moves, the ETF follows within milliseconds and the constituent stocks within a little more; who leads depends on the hour, the venue and the size of the move, and it has changed as the fastest firms have caught up.
- **Sections.** Price discovery across markets; Information shares; Estimating lag on asynchronous ticks; Trading the lead: quoting and taking; When the leader changes.
- **Defines.** information share, component share, cross-venue lead.
- **Uses (defined earlier).** lead--lag relationship (B7.10), lead--lag estimator (B7.10), Hayashi--Yoshida estimator (B4.21), Epps effect (B4.21), cointegration (B4.20), vector error-correction model (B4.20), futures-to-cash lead (B7.10), primary venue (B2.14), market maker (B1.1), bid--ask spread (B1.1), adverse selection (B1.1), mid price (B1.1), inventory (B2.30).
- **Strategy files.** index future to ETF; ETF to constituents; cash Treasury to Treasury futures; leading crypto venue to lagging venue; primary FX venue to secondary platforms.
- **Tutorial.** Measure Hayashi--Yoshida lead-lag and Hasbrouck information shares on firm_tape pairs with known latency, recover the planted lag, then trade the lead as a quoter and as a taker with execution latency in firm.mmharness.
- **Build.** `firm.xvenue`: information and component shares from a vector error-correction fit, lag estimation on firm.leadlag, a lead-follower simulator with per-venue latency; Python.
- **Weekend problem.** Who moves first — named result: the planted and estimated lead, the leader's information share, and the P&L of trading the lead at the latency where it disappears.
- **Facts to verify.** Hasbrouck 1995 One security, many markets (JF); Gonzalo and Granger 1995 Estimation of common long-memory components in cointegrated systems (JBES); Hasbrouck 2003 Intraday price formation in US equity index markets (JF); Huth and Abergel 2014 High frequency lead/lag relationships -- empirical facts (JEF); Makarov and Schoar 2020 Trading and arbitrage in cryptocurrency markets (JFE).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Hasbrouck (1995): contributions of several markets to price discovery of one security measured by information shares from a vector error-correction model | J. Hasbrouck, "One security, many markets: determining the contributions to price discovery", Journal of Finance 50(4), 1995, 1175-1199 | https://doi.org/10.1111/j.1540-6261.1995.tb04054.x | 2026-09-25 | Crossref metadata | §2 |
| F2 | Gonzalo and Granger (1995): permanent-transitory decomposition of cointegrated systems (the component share) | J. Gonzalo and C. Granger, "Estimation of common long-memory components in cointegrated systems", Journal of Business and Economic Statistics 13(1), 1995, 27-35 | https://doi.org/10.1080/07350015.1995.10524576 | 2026-09-25 | Crossref metadata | §2 |
| F3 | Hasbrouck (2003): for the S&P 500 and Nasdaq-100 most price discovery occurs in the E-mini futures; for the S&P 400 it is shared between the regular future and the ETF; the S&P 500 ETF contributes markedly to price discovery in sector ETFs, with only minor effects the other way | J. Hasbrouck, "Intraday price formation in U.S. equity index markets", Journal of Finance 58(6), 2003 | https://doi.org/10.1046/j.1540-6261.2003.00609.x | 2026-09-25 | OpenAlex abstract | strat:hf:lead-lag-and-cross-venue-trading:future, strat:hf:lead-lag-and-cross-venue-trading:etf |
| F4 | Mizrach and Neely (2008): futures markets' previously neglected role in US Treasury price discovery; 5- and 10-year GovPX spot information shares typically fail to reach 50% from 1999 on | B. Mizrach and C. J. Neely, "Information shares in the US Treasury market", Journal of Banking and Finance 32(7), 2008, 1221-1233 | https://ideas.repec.org/a/eee/jbfina/v32y2008i7p1221-1233.html | 2026-09-25 | "The estimates of 5- and 10-year GovPX spot market information shares typically fail to reach 50% from 1999 on" | strat:hf:lead-lag-and-cross-venue-trading:treasury |
| F5 | Makarov and Schoar (2020): large, recurrent arbitrage opportunities across crypto exchanges; deviations much larger across than within countries; the common component of signed volume explains 80% of bitcoin returns, idiosyncratic components help explain arbitrage spreads | I. Makarov and A. Schoar, "Trading and arbitrage in cryptocurrency markets", Journal of Financial Economics 135(2), 2020, 293-319 | https://doi.org/10.1016/j.jfineco.2019.07.001 | 2026-09-25 | Crossref metadata; abstract via SSRN/IDEAS search summary | strat:hf:lead-lag-and-cross-venue-trading:crypto |
| F6 | Chaboud, Chiquoine, Hjalmarsson and Vega (2014): algorithmic trading in FX (EBS data) reduced triangular arbitrage opportunities, mainly through computers taking liquidity; evidence of highly correlated algorithmic strategies | A. Chaboud et al., "Rise of the machines: algorithmic trading in the foreign exchange market", Journal of Finance 69(5), 2014, 2045-2084 | https://doi.org/10.1111/jofi.12186 | 2026-09-25 | Crossref abstract | strat:hf:lead-lag-and-cross-venue-trading:fx |
| F7 | Budish, Cramton and Shim (2015): ES-SPY median return correlation 0.1016 at 10 ms and 0.0080 at 1 ms (2011); median arbitrage duration 97 ms (2005) to 7 ms (2011) | QJE 130(4), 2015 (authors' PDF) | https://www.cramton.umd.edu/papers2015-2019/budish-cramton-shim-hft-frequent-batch-auctions.pdf | 2026-09-25 | pdftotext quotes as in chapter 7's ledger F4 | §1, strat:hf:lead-lag-and-cross-venue-trading:future |

## EXCLUDED

- Huth and Abergel (2014): not needed for any claim; dropped.
- Leads between named venues today (which crypto venue leads, which FX platform): volatile and unpublished in citable form; the strategy files state the mechanism only.

