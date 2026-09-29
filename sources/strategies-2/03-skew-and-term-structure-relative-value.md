# 3. Skew and Term-Structure Relative Value — brief and source ledger

## Brief

- **Hook.** Two options on the same index, one a month out and one three months out, can disagree about the same future; relative-value traders bet on the disagreement rather than on the level.
- **Sections.** Trading the smile; Trading the term structure; Across related underlyings; Risk: what a relative-value vol book is really short.
- **Defines.** skew trade, term-structure trade, cross-underlying volatility spread.
- **Uses (defined earlier).** volatility skew (B1.25), term structure of volatility (B1.25), volatility surface (B5.7), risk reversal (B2.19), sticky strike (B5.7), sticky delta (B5.7), implied volatility (B1.25), realised volatility (B1.25), delta hedging (B1.26), vega (B5.4), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** skew flattener; calendar volatility spread; index-versus-ETF volatility spread; cross-market volatility spread.
- **Tutorial.** Fit firm.synthvol surfaces each day, build skew and calendar trades hedged in vega and delta, and measure how much of their P&L comes from the planted mean reversion of skew and slope and how much from the level.
- **Build.** `firm.volrv`: surface-feature extraction (level, skew, curvature, slope), vega-neutral relative-value trades and their P&L attribution; Python.
- **Weekend problem.** Same future, two prices — named result: the skew and calendar trades' Sharpe ratios and the share of their P&L that is really level exposure.
- **Facts to verify.** Bakshi, Kapadia, Madan 2003 stock return characteristics, skew laws (RFS); Kelly, Pastor, Veronesi 2016 the price of political uncertainty (JF) or equivalent term-structure evidence.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | G. Bakshi, N. Kapadia, D. Madan, "Stock return characteristics, skew laws, and the differential pricing of individual equity options", Review of Financial Studies 16(1) (2003) 101-143: with OEX options and 30 stocks, individual stocks' risk-neutral distributions are far less negatively skewed than the market index's; risk aversion introduces skewness in the risk-neutral density; skew laws decompose individual skewness into systematic and idiosyncratic parts | Crossref metadata; OpenAlex abstract | https://doi.org/10.1093/rfs/16.1.0101 | 2026-09-25 | abstract: "individual risk-neutral distributions differ from that of the market index by being far less negatively skewed" | section 1; section 3; strat:s2:skew-and-term-structure-relative-value:etf; omsources |
| F2 | T. L. Johnson, "Risk premia and the VIX term structure", Journal of Financial and Quantitative Analysis 52(6) (2017) 2461-2490: the shape of the VIX term structure conveys information about the price of variance risk rather than expected changes in VIX (a rejection of the expectations hypothesis); its second principal component, SLOPE, predicts excess returns of synthetic S&P 500 variance swaps, VIX futures and S&P 500 straddles | Crossref metadata; OpenAlex abstract | https://doi.org/10.1017/s0022109017000825 | 2026-09-25 | abstract: "The shape of the ... VIX term structure conveys information about the price of variance risk rather than expected changes in the VIX"; "SLOPE, summarizes nearly all this information, predicting the excess returns of synthetic ... variance swaps, VIX futures, and ... straddles" | section 2; strat:s2:skew-and-term-structure-relative-value:calendar; omsources |
| F3 | Cboe SKEW Index white paper (2011): SKEW is derived from S, the price of S&P 500 skewness computed from a portfolio of S&P 500 options, as SKEW = 100 - 10 S; it rises as S becomes more negative and tail risk increases; a strike-independent measure of the slope of the implied volatility curve; low correlation between variations in SKEW and VIX | Cboe document (pdftotext) | https://cdn.cboe.com/resources/indices/documents/SKEWwhitepaperjan2011.pdf | 2026-09-25 | "SKEW = 100 – 10 * S"; "SKEW increases as S becomes more negative and tail risk increases"; "the low correlation between variations in SKEW and VIX" | section 1 |
| F4 | Cboe VIX, VIX3M (from September 2009), SKEW (from January 1990), RVX and VXN daily histories to 22 September 2026, used only through derived statistics (VXN is Cboe's volatility index on the Nasdaq-100) | Cboe daily price files | https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv ; VIX3M_History.csv ; SKEW_History.csv ; RVX_History.csv ; VXN_History.csv | 2026-09-25 | files downloaded; statistics recomputed by s2_fetch_term.py | hook; section 1; section 2; section 3 |

## EXCLUDED

- Kelly, Pastor, Veronesi 2016 (political uncertainty): not needed; Johnson 2017 is the term-structure evidence used.
- Any performance figure for skew, calendar or cross-index volatility funds or desks: none found in a citable source; none quoted.
- Bid-ask spreads of index options in vol points: no source fetched; the chapter's cost (one percent of vol per leg) is its own assumption and is stated as such.
- The synthetic surface's noises, half-lives and level dependence are the chapter's own choices.

