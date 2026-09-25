# 2. Dispersion and Correlation — brief and source ledger

## Brief

- **Hook.** An index option is priced as if its constituents move together more than they do: selling index volatility and buying the members' collects the gap, until a crash makes everything move as one.
- **Sections.** Index volatility from member volatilities; The correlation risk premium; Dispersion trades and their weights; When correlation goes to one.
- **Defines.** correlation risk premium, realised correlation, dispersion weighting.
- **Uses (defined earlier).** dispersion trade (B5.17), implied correlation (B5.17), correlation swap (B5.17), implied volatility (B1.25), realised volatility (B1.25), delta hedging (B1.26), vega (B5.4), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** vega-weighted dispersion; theta-weighted dispersion; correlation swap short; sector dispersion.
- **Tutorial.** On firm.synthvol's index and thirty members with a planted correlation risk premium, measure implied against realised correlation and run dispersion books with different weightings through the planted crash.
- **Build.** `firm.dispersion`: implied and realised correlation, dispersion trade construction and weighting, P&L decomposition into correlation and volatility parts; Python.
- **Weekend problem.** When everything moves together — named result: the dispersion book's return from the correlation premium and its loss when correlation jumps.
- **Facts to verify.** Driessen, Maenhout, Vilkov 2009 the price of correlation risk (JF); Cboe implied correlation index methodology (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | J. Driessen, P. J. Maenhout, G. Vilkov, "The price of correlation risk: evidence from equity options", Journal of Finance 64(3) (2009) 1377-1406: with S&P 100 index options, options on all components and stock returns, evidence of priced correlation risk from index and individual variance risk; a strategy exploiting it has a high alpha for CRRA investors without frictions; correlation risk exposure explains the cross-section of index and individual option returns; the correlation risk premium cannot be exploited with realistic trading frictions (limits to arbitrage) | Crossref metadata; OpenAlex abstract | https://doi.org/10.1111/j.1540-6261.2009.01467.x | 2026-09-25 | abstract: "A trading strategy exploiting priced correlation risk generates a high alpha"; "The correlation risk premium cannot be exploited with realistic trading frictions" | hook; section 2; strat:s2:dispersion-and-correlation:vega; omsources |
| F2 | Cboe S&P 500 Implied Correlation Index methodology: the expected average correlation of S&P 500 components implied through SPX option prices and single-stock options on the 50 largest components; derived from the index variance as the weighted sum of component variances and pairwise covariances; the 3-month index uses the top 50 value-weighted stocks and Markowitz's risk decomposition; a smoothed realised correlation is in most cases slightly below the implied | Cboe documents (pdftotext) | https://cdn.cboe.com/resources/indices/documents/impliedcorrelationindicator.pdf ; https://cdn.cboe.com/resources/indices/documents/Cboe_USO_ImpliedCorrelation_0421_v2.0.2.pdf | 2026-09-25 | "implied through SPX option prices and prices of single-stock options on the 50 largest components of the SPX"; "the realized correlation is in most cases slightly below the Cboe 3M Implied Correlation Index" | section 1; section 2 |
| F3 | Cboe COR1M (from January 2006) and DSPX (from June 2014) daily histories to 22 September 2026, used only through derived statistics | Cboe daily price files | https://cdn.cboe.com/api/global/us_indices/daily_prices/COR1M_History.csv ; https://cdn.cboe.com/api/global/us_indices/daily_prices/DSPX_History.csv | 2026-09-25 | files downloaded; statistics recomputed by s2_fetch_cor.py | hook; section 2; section 4 |

## EXCLUDED

- The DSPX methodology (what the dispersion index measures exactly): not fetched; the chapter reports its statistics as the index Cboe publishes and says no more.
- Performance of dispersion funds or bank dispersion desks: none named or quoted.
- The synthetic premia (index 1.30, members 1.10 on expected variance) are the chapter's own choices.
