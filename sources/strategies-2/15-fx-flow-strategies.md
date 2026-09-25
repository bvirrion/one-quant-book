# 15. FX Flow Strategies — brief and source ledger

## Brief

- **Hook.** At four in the afternoon London time the benchmark rates for currencies are fixed on the trades of a few minutes; funds that must trade at the fix create flows that others can anticipate.
- **Sections.** The fix and its flows; Month-end rebalancing; Central-bank behaviour; Trading predictable flows.
- **Defines.** fix flow, rebalancing-flow estimate, central-bank reaction trade.
- **Uses (defined earlier).** benchmark fix (B2.17), month-end rebalancing (B2.17), fixing window (B2.17), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** month-end hedge-rebalancing flow; fix-window liquidity provision; central-bank intervention fade; equity-performance FX hedge flow.
- **Tutorial.** Estimate month-end FX hedge-rebalancing flows from synthetic equity performance by country and trade ahead of them; simulate fix-window price pressure.
- **Build.** `firm.fxflows`: month-end flow estimator from asset performance and hedge ratios, fix-window pressure model and flow trades; Python.
- **Weekend problem.** Four o'clock — named result: the month-end flow trade's return against the estimated flow size.
- **Facts to verify.** Melvin and Prins 2015 equity hedging and exchange rates at the London 4 p.m. fix (J. Financial Markets); Evans 2018 forex trading and the WMR fix (JBF); FCA 2014 FX benchmark enforcement (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | M. Melvin, J. Prins, "Equity hedging and exchange rates at the London 4 p.m. fix", Journal of Financial Markets 22 (2015) 50-72: tests the hedging channel of exchange-rate adjustment; the London 4 p.m. fix identifies when hedging trades concentrate and past equity returns their direction; equity market appreciation over the month predicts currency depreciation before the end-of-month fix | Crossref metadata; RePEc abstract | https://doi.org/10.1016/j.finmar.2014.11.001 | 2026-09-25 | "equity market appreciation over the month can be used to predict currency depreciation before the end-of-month fix" | hook; section 2; strat:s2:fx-flow-strategies:monthend; omsources |
| F2 | M. D. D. Evans, "Forex trading and the WMR Fix", Journal of Banking & Finance 87 (2018) 233-247: banks were fined for trading around the 4:00 p.m. WMR Fix; across 21 currencies over a decade, forex price changes show extraordinary volatility and negative serial correlation around the Fix, contrary to a competitive microstructure model | Crossref metadata; RePEc abstract | https://doi.org/10.1016/j.jbankfin.2017.09.017 | 2026-09-25 | "forex price changes display extraordinary volatility and negative serial correlation around the Fix" | section 1; strat:s2:fx-flow-strategies:fix; omsources |
| F3 | Financial Conduct Authority press release, 12 November 2014: fines totalling GBP 1,114,918,000 on Citibank N.A. (GBP 225,575,000), HSBC Bank plc (GBP 216,363,000), JPMorgan Chase Bank N.A. (GBP 222,166,000), The Royal Bank of Scotland plc (GBP 217,000,000) and UBS AG (GBP 233,814,000) for G10 spot FX failings between 1 January 2008 and 15 October 2013: traders shared confidential client information and attempted to manipulate fix rates, including the 4 p.m. WM/Reuters and ECB fixes, and to trigger client stop-loss orders | FCA press release (page text via WebFetch) | https://www.fca.org.uk/news/press-releases/fca-fines-five-banks-%C2%A311-billion-fx-failings-and-announces-industry-wide-remediation-programme | 2026-09-25 | "attempted to manipulate fix rates and trigger client 'stop loss' orders"; "They shared information about clients' activities which they had been trusted to keep confidential" | section 1; section 4 |
| F4 | FRED H.10 noon New York exchange rates (EUR, GBP, JPY, CHF, AUD, CAD) and the Cboe S&P 500 index history, 1999-2026, used only through derived statistics | FRED; Cboe daily price files | https://fred.stlouisfed.org/series/DEXUSEU (and the others) ; https://cdn.cboe.com/api/global/us_indices/daily_prices/SPX_History.csv | 2026-09-25 | files downloaded; statistics recomputed by s2_fetch_monthend.py | section 2 |

## EXCLUDED

- The WM/Reuters fix methodology (window length and its 2015 change): not fetched; the chapter says only "a short window around 4 p.m.".
- Central-bank intervention records (e.g. Japan's Ministry of Finance): not fetched; the central-bank section states mechanisms and cites no episode.
- Fix-rate data: licensed; the chapter's real test uses noon New York H.10 rates, which is stated.

