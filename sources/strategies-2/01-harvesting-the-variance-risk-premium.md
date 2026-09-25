# 1. Harvesting the Variance Risk Premium — brief and source ledger

## Brief

- **Hook.** Selling index volatility has paid on most days for decades, because implied volatility usually exceeds the volatility that follows; its losses arrive together, in days, and have closed funds.
- **Sections.** The premium and why it exists; Implementations: options, variance swaps, overwriting; Delta-hedged option returns; Blow-ups and how to size for them.
- **Defines.** short-volatility strategy, delta-hedged option return, option overwriting.
- **Uses (defined earlier).** variance risk premium (B5.14), variance swap (B5.14), straddle (B5.4), volatility index (B1.25), implied volatility (B1.25), realised volatility (B1.25), delta hedging (B1.26), vega (B5.4), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** short index variance; delta-hedged short straddle; covered-call overwriting; put writing; volatility-targeted short volatility.
- **Tutorial.** Build firm.synthvol, a synthetic index with stochastic volatility, jumps and an implied-volatility surface carrying a planted variance risk premium; run short-volatility implementations and size them against the planted crash.
- **Build.** `firm.synthvol` (synthetic index and single-stock option market: stochastic variance with jumps, implied surfaces with a planted premium, deterministic) and `firm.shortvol` (short-volatility implementations with delta hedging and sizing); Python.
- **Weekend problem.** Picking up nickels — named result: the short-variance book's Sharpe ratio before its worst month and its loss in that month, by leverage.
- **Facts to verify.** Carr and Wu 2009 variance risk premiums (RFS); Bakshi and Kapadia 2003 delta-hedged gains and the negative market volatility risk premium (RFS); Cboe S&P 500 BuyWrite and PutWrite indices (dated); February 2018 XIV termination (as B1/B5 where sourced).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | P. Carr, L. Wu, "Variance risk premiums", Review of Financial Studies 22(3) (2009, online 2008) 1311-1341: the risk-neutral expected return variance (the variance swap rate) is well approximated by a portfolio of options; the difference between realised variance and this synthetic variance swap rate quantifies the variance risk premium; applied to five stock indexes and 35 individual stocks | Crossref metadata; OpenAlex abstract | https://doi.org/10.1093/rfs/hhn038 | 2026-09-25 | abstract: "We propose to use the difference between the realized variance and this synthetic variance swap rate to quantify the variance risk premium" | section 1; strat:s2:harvesting-the-variance-risk-premium:variance; omsources |
| F2 | G. Bakshi, N. Kapadia, "Delta-hedged gains and the negative market volatility risk premium", Review of Financial Studies 16(2) (2003) 527-566: in S&P 500 index options, a delta-hedged long option underperforms zero; the underperformance is smaller away from the money and greater when volatility is higher; the volatility risk premium affects delta-hedged gains after accounting for jump fears; evidence of a negative market volatility risk premium | Crossref metadata; OpenAlex abstract | https://doi.org/10.1093/rfs/hhg002 | 2026-09-25 | abstract: "First, the delta-hedged strategy underperforms zero. Second, the documented underperformance is less for options away from the money. Third, the underperformance is greater at times of higher volatility" | section 3; strat:s2:harvesting-the-variance-risk-premium:straddle; omsources |
| F3 | Cboe VIX, S&P 500 (SPX), S&P 500 PutWrite (PUT) and BuyWrite (BXM) daily index histories to 22 September 2026, used only through derived statistics (data/strategies-2/LICENSES.md) | Cboe Global Markets daily price files | https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv ; https://cdn.cboe.com/api/global/us_indices/daily_prices/PUT_History.csv ; https://cdn.cboe.com/api/global/us_indices/daily_prices/BXM_History.csv ; https://cdn.cboe.com/api/global/us_indices/daily_prices/SPX_History.csv | 2026-09-25 | files downloaded; statistics recomputed by s2_fetch_cboe.py | hook; section 1; section 2; strat:s2:harvesting-the-variance-risk-premium:overwrite; strat:s2:harvesting-the-variance-risk-premium:putwrite |

## EXCLUDED

- Funds closed by short-volatility losses (the brief's hook): not sourced here; February 2018's exchange-traded products are chapter 5's.
- The PUT and BXM index methodologies (strikes, roll dates, collateral): not fetched; the chapter describes the indices only by name and by their derived statistics, and notes that SPX is a price index without dividends.
- The synthetic market's parameters and crashes are the chapter's own choices.
