# 6. Zero-Day Options and Dealer-Gamma Flows — brief and source ledger

## Brief

- **Hook.** Options that expire the day they are bought now trade in volumes comparable to the rest of the S&P 500 option market; the dealers who sell them hedge within the day, and their hedging can pin or push the index.
- **Sections.** Zero-day options and who trades them; Estimating dealer gamma; Pinning and pushing; Trading the hedging flow.
- **Defines.** gamma exposure estimate, gamma flip level, pinning.
- **Uses (defined earlier).** zero-day option (B1.26), dealer gamma (B1.26), end-of-day hedging flow (B8.13), pin risk (B1.23), implied volatility (B1.25), realised volatility (B1.25), delta hedging (B1.26), vega (B5.4), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** long gamma below the flip level; pin trade near large strikes; intraday dealer-hedging momentum.
- **Tutorial.** Simulate an intraday index with dealers short or long gamma from zero-day options, estimate their exposure from open interest by strike with noise in the assumed dealer side, and trade the implied hedging flow.
- **Build.** `firm.gammaflow`: dealer gamma estimation from open interest by strike under side assumptions, flip-level and pin statistics, and an intraday hedging-feedback simulator; Python.
- **Weekend problem.** Who is short gamma — named result: the error of the gamma estimate when the dealers' side is guessed, and the hedging-flow trade's return by regime.
- **Facts to verify.** Cboe 0DTE volume statistics (dated); Baltussen, Da, Lammers, Martens 2021 hedging demand and market intraday momentum (JFE); Ni, Pearson, Poteshman, White 2021 does option trading have a pervasive impact on underlying stock prices? (RFS).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Cboe, full-year 2025 trading volume release: SPX zero-days-to-expiry (0DTE) options ADV record of 2.3 million contracts, representing 59% of total SPX volume | Cboe investor relations release (page text via WebFetch) | https://ir.cboe.com/news/news-details/2026/Cboe-Global-Markets-Reports-Trading-Volume-for-December-and-Full-Year-2025/default.aspx | 2026-09-25 | "SPX zero-days-to-expiry (0DTE) options ADV record of 2.3 million contracts, representing 59% of total SPX volume" | dat:s2:zero-day-options-and-dealer-gamma-flows:volume; hook |
| F2 | Cboe Insights, 2 September 2025, "SPX 0DTE options jump to record 62% share in August": in August 2025 0DTE made up a record 62.4% of overall SPX volume, averaging about 2.4 million contracts a day, with retail traders an estimated 53% of the volume | Cboe insights post (page text via WebFetch) | https://www.cboe.com/insights/posts/spx-0-dte-options-jump-to-record-62-share-in-august/ | 2026-09-25 | "now making up a record 62.4% of overall SPX volume"; "averaging ~2.4M contracts a day"; "retail traders making up an estimated 53% of the volume" | dat:s2:zero-day-options-and-dealer-gamma-flows:volume; section 1 |
| F3 | G. Baltussen, Z. Da, S. Lammers, M. Martens, "Hedging demand and market intraday momentum", Journal of Financial Economics 142(1) (2021) 377-403: hedging short gamma exposure requires trading in the direction of price moves, creating momentum; with intraday returns on over 60 futures (equities, bonds, commodities, currencies), 1974-2020, strong market intraday momentum everywhere; the return in the last 30 minutes before the close is positively predicted by the return over the rest of the day (from the previous close); highly significant, reverts over the next days; linked to the gamma hedging demand of option market makers and leveraged ETFs | Crossref metadata; RePEc abstract | https://doi.org/10.1016/j.jfineco.2021.04.029 ; https://ideas.repec.org/a/eee/jfinec/v142y2021i1p377-403.html | 2026-09-25 | "The return during the last 30 minutes before the market close is positively predicted by the return during the rest of the day"; "links market intraday momentum to the gamma hedging demand from market participants such as market makers of options and leveraged ETFs" | hook; section 4; strat:s2:zero-day-options-and-dealer-gamma-flows:momentum; omsources |
| F4 | S. X. Ni, N. D. Pearson, A. M. Poteshman, J. White, "Does option trading have a pervasive impact on underlying stock prices?", Review of Financial Studies 34(4) (2021) 1952-1986: evidence of a noninformational channel through which option market maker hedge rebalancing affects stock return volatility and the probability of large stock price moves | Crossref metadata; OpenAlex abstract | https://doi.org/10.1093/rfs/hhaa082 | 2026-09-25 | "a noninformational channel through which option market maker hedge rebalancing affects stock return volatility and the probability of large stock price moves" | section 3; omsources |

## EXCLUDED

- Published "gamma exposure" (GEX) figures from data vendors and newsletters: not citable; the chapter builds its own estimate and measures its error on synthetic data.
- The claim that dealers are systematically long calls and short puts: stated only as the convention analysts use, not as a fact about dealers.
- Pinning evidence on expiration dates (Ni, Pearson, Poteshman 2005, JFE): not fetched; the chapter reports that its own model produces no pinning and says why.
- Costs of 1 basis point a round trip for the index trade: the chapter's own assumption.

