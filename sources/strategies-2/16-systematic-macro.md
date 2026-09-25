# 16. Systematic Macro — brief and source ledger

## Brief

- **Hook.** Value, momentum and carry, measured country by country in bonds, currencies and equity indices, make a macro portfolio that no economist designed and that has earned more than most who did.
- **Sections.** Signals across countries and assets; Macro-data signals; Combining signals; What the record shows.
- **Defines.** macro value signal, macro momentum, economic-surprise signal.
- **Uses (defined earlier).** time-series momentum (B8.19), carry strategy (B8.20), diversified carry (B8.20), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** cross-country value; macro momentum; carry across asset classes; economic-surprise tilt; combined macro factor portfolio.
- **Tutorial.** On firm.synthfut's equity, bond and currency markets, add planted value (mean reversion to fair value) and macro-data effects, build value, momentum, carry and macro-surprise signals and combine them.
- **Build.** `firm.sysmacro`: cross-asset value, momentum, carry and macro-surprise signals and their combination with risk budgets; Python.
- **Weekend problem.** Designed by no one — named result: each signal's Sharpe ratio and the combination's, with the correlations that make it work.
- **Facts to verify.** Asness, Moskowitz, Pedersen 2013 value and momentum everywhere (JF); Brooks 2017 a half century of macro momentum (AQR) or peer-reviewed equivalent.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | C. S. Asness, T. J. Moskowitz, L. H. Pedersen, "Value and momentum everywhere", Journal of Finance 68(3) (2013) 929-985: consistent value and momentum return premia across eight diverse markets and asset classes and a strong common factor structure; value and momentum returns correlate more across asset classes than passive exposures, and value and momentum are negatively correlated with each other within and across asset classes; global funding liquidity risk is a partial source | Crossref metadata; OpenAlex abstract | https://doi.org/10.1111/jofi.12021 | 2026-09-25 | abstract: "consistent value and momentum return premia across eight diverse markets and asset classes"; "value and momentum are negatively correlated with each other, both within and across asset classes" | hook; section 1; section 4; strat:s2:systematic-macro:value; omsources |
| F2 | J. Brooks, "A half century of macro momentum", AQR white paper (10 August 2017): macro momentum is a systematic global macro strategy long assets whose fundamental macroeconomic trends are improving and short those whose trends are deteriorating; described as having the potential for strong returns with low correlation to traditional asset classes, with diversification in bear equity markets and rising-yield environments | AQR web page (page text via WebFetch) | https://www.aqr.com/Insights/Research/White-Papers/A-Half-Century-of-Macro-Momentum | 2026-09-25 | "a systematic global macro strategy that takes long positions in assets for which fundamental macroeconomic trends are improving and short positions in assets for which fundamental macroeconomic trends are deteriorating" | section 2; strat:s2:systematic-macro:momentum; omsources |

## EXCLUDED

- Performance statistics of Brooks's macro momentum (Sharpe ratios, sample): in the PDF, not fetched; only the page's description is used.
- Named managers' systematic macro returns: none quoted.
- The chapter uses no real market data: every number about the book is from the synthetic market, whose planted effects (value gap, surprise index, their sizes) are the chapter's own choices.

