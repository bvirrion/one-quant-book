# 7. Tail Hedging and Long Volatility — brief and source ledger

## Brief

- **Hook.** A tail hedge that bleeds a little every month is the most disliked position in a portfolio for years, until the month it pays for all of them; whether it was worth its cost depends on what it lets the rest of the portfolio do.
- **Sections.** The cost of convexity; Put programmes and their monetisation; Alternatives: trend, long vol, variance; Judging a hedge by the portfolio.
- **Defines.** tail hedge, hedge monetisation, hedge bleed.
- **Uses (defined earlier).** crisis alpha (B8.19), variance risk premium (B5.14), collar (B3.12), implied volatility (B1.25), realised volatility (B1.25), delta hedging (B1.26), vega (B5.4), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** rolling out-of-the-money put programme; put spread collar; long variance with monetisation.
- **Tutorial.** On firm.synthvol run put programmes with different strikes, tenors and monetisation rules, combine them with an equity portfolio, and compare the portfolio's growth rate and drawdown with and without the hedge and with a trend overlay.
- **Build.** `firm.tailhedge`: rolling option programmes with monetisation rules, their cost and payoff, and portfolio-level evaluation (growth, drawdown, rebalancing benefit); Python.
- **Weekend problem.** Paying for the month that pays — named result: the hedge's annual bleed and the portfolio growth rate with and without it.
- **Facts to verify.** Israelov 2019 pathetic protection: the elusive benefits of protective puts (J. Alternative Investments); Harvey et al. 2019 the best of strategies for the worst of times (JPM).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | R. Israelov, "Pathetic protection: the elusive benefits of protective puts", Journal of Alternative Investments 21(3) (2019) 6-33: in the typical use case put options are quite ineffective at reducing drawdowns versus statically reducing exposure; studied via simulation and the CBOE S&P 500 5% Put Protection Index; unless purchases and maturities are timed just right around drawdowns, they may offer little protection and can increase drawdowns and volatility per unit of expected return | Crossref metadata; OpenAlex abstract | https://doi.org/10.3905/jai.2018.1.066 | 2026-09-25 | abstract: "put options are quite ineffective at reducing drawdowns versus the simple alternative of statically reducing exposure"; "Unless option purchases and their maturities are timed just right around equity drawdowns, they may offer little downside protection" | hook; section 1; section 4; strat:s2:tail-hedging-and-long-volatility:puts; omsources |
| F2 | C. R. Harvey, E. Hoyle, S. Rattray, M. Sargaison, D. Taylor, O. Van Hemert, "The best of strategies for the worst of times: can portfolios be crisis proofed?", Journal of Portfolio Management 45(5) (2019) 7-28: continuously holding short-dated S&P 500 puts is the most reliable defensive method but the most costly; Treasuries carry positively but may be unreliable since the negative bond-equity correlation after 2000 is a historical rarity; gold and credit protection sit between; futures time-series momentum and quality long-short did well in past drawdowns | Crossref metadata; OpenAlex abstract | https://doi.org/10.3905/jpm.2019.45.5.007 | 2026-09-25 | abstract: "continuously holding short-dated S&P 500 put options is the most reliable defensive method but also the most costly strategy"; "futures time-series momentum (which benefits from extended equity sell-offs)" | section 3; strat:s2:tail-hedging-and-long-volatility:variance; omsources |
| F3 | Cboe S&P 500 Put Protection Indices methodology: PPUT tracks a hypothetical strategy holding the S&P 500 and buying monthly 5% out-of-the-money SPX puts, rolled on the third Friday; the indices are total return indices (dividends reinvested) | Cboe methodology PDF (pdftotext) | https://cdn.cboe.com/api/global/us_indices/governance/Cboe_SP_500_Put_Protection_Indices_Methodology.pdf | 2026-09-25 | "The Indices are total return indices"; "Roll Date: Third Friday of each month" | section 2 |
| F4 | Cboe Insights, 15 July 2021, "Hedging downside exposure with PPUT, CLL and CLLZ indices": CLLZ holds the S&P 500, buys a 2.5%-5% SPX put spread monthly and sells a monthly OTM SPX call to cover its cost; over June 1986 to June 2021 PPUT had 18 monthly declines of 6% or more against 35 for the S&P 500 | Cboe insights post (page text via WebFetch) | https://www.cboe.com/insights/posts/benchmark-indices-series-hedging-downside-exposure-with-pput-cll-and-cllz-indices/ | 2026-09-25 | "buys a 2.5% - 5% SPX put spread on a monthly basis; and sells a monthly OTM SPX call option to cover the cost of the put spread" | section 2; strat:s2:tail-hedging-and-long-volatility:collar |
| F5 | Cboe PPUT, CLLZ and SPX daily histories, 30 June 1986 to 22 September 2026, used only through derived statistics | Cboe daily price files | https://cdn.cboe.com/api/global/us_indices/daily_prices/PPUT_History.csv ; CLLZ_History.csv ; SPX_History.csv | 2026-09-25 | files downloaded; statistics recomputed by s2_fetch_protect.py | section 2 |

## EXCLUDED

- A total-return S&P 500 series: Cboe's free files do not include one; PPUT and CLLZ (total return) are compared with the SPX price index for drawdowns only, and the return gap is stated to understate their cost.
- Performance of named tail-risk funds: none quoted.
- The synthetic smile for this chapter (skew -0.25, curvature 0.02) and the three planted crashes are the chapter's own choices.

