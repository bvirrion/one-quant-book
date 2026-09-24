# 17. Multi-Asset Options — brief and source ledger

## Brief

- **Hook.** A note pays its coupon only while all three of its shares stay above 70% of their start; the client sees three familiar names, the dealer a correlation position that no listed market quotes.
- **Sections.** Correlation and baskets; Worst-of and best-of; Implied correlation, dispersion and correlation skew; Local correlation; Quanto and composite options.
- **Defines.** basket option, worst-of option, best-of option, implied correlation, dispersion trade, correlation swap, correlation skew, local correlation, quanto option, quanto adjustment, composite option.
- **Uses (defined earlier).** volatility skew (Book 1 ch. 25), base correlation (Book 2 ch. 24), Black--Scholes model (ch. 3), local volatility, Markovian projection (ch. 9), Cholesky factorisation (Book 4 ch. 25), Monte Carlo (Book 4 ch. 26), Girsanov's theorem (Book 4 ch. 5), cross-gamma (Book 6 ch. 3), copula (Book 4 ch. 15), Gaussian copula (Book 6 ch. 15), spread option (Book 6 ch. 16).
- **Tutorial.** Price a basket and a worst-of by Monte Carlo against moment matching, compute the implied correlation of a synthetic index and its members at three strikes, and measure the quanto adjustment on an index forward paid in another currency.
- **Build.** `firm.multiasset`: correlated multi-asset path generator (Cholesky, per-asset local volatility, quanto drift) with basket, worst-of and quanto payoffs.
- **Weekend problem.** The index and its members — named result: the implied correlation of a synthetic 20-stock index at three strikes, and the P&L of a dispersion trade when realised correlation comes in 15 points below implied.
- **Facts to verify.** Cboe implied correlation index methodology; Driessen, Maenhout, Vilkov 2009 JF 'The price of correlation risk'; CME Nikkei 225 USD futures (quanto) contract spec; Reghai 2006 / Langnau 2010 local correlation; Bossu 2005 correlation swaps.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Driessen, Maenhout and Vilkov, "The price of correlation risk: evidence from equity options" (SSRN 673425, 2005): S&P 100 index options, options on all components and stock returns; evidence of priced correlation risk; the correlation risk premium cannot be exploited with realistic trading frictions | Crossref record with abstract, 10.2139/ssrn.673425 | https://api.crossref.org/works/10.2139/ssrn.673425 | 2026-09-24 | abstract in Crossref | sec. implied correlation, omsources |
| F2 | Average option-implied correlation 39.5% (S&P 500) and 46.0% (DJ30) against realised 32.5% and 35.5%: evidence of a large negative correlation risk premium; the index variance risk premium attributed to the price of correlation risk | Driessen, Maenhout and Vilkov, "Option-implied correlations and the price of correlation risk" (SSRN 2359380, 2013), abstract | https://api.crossref.org/works/10.2139/ssrn.2359380 | 2026-09-24 | abstract in Crossref | sec. implied correlation, dispersion |
| F3 | Index options encode non-trivial dependence between constituents: a Gaussian copula of the single-stock distributions fails to explain the steepness of the index skew; index options price higher correlations in stress scenarios; a local correlation model extends multi-asset local volatility and fits index and constituent options by construction | Langnau, "Introduction into 'Local correlation modelling'", arXiv 0909.3441 (2009) | https://arxiv.org/abs/0909.3441 | 2026-09-24 | abstract (arXiv API) | sec. local correlation, omsources |

## EXCLUDED

- Cboe implied correlation index methodology: the methodology PDFs returned 403 and the dashboard page carries no methodology text (2026-09-24); the chapter gives the standard formula without attributing it to an index provider.
- CME Nikkei 225 (USD) futures specification: cmegroup.com returned 403; the quanto example is generic.
- Reghai (2006) and Bossu (2005) on local correlation and correlation swaps: no fetchable record.
- The published journal version of Driessen, Maenhout and Vilkov (Journal of Finance 2009): the Crossref DOI guessed from memory resolved to a different paper; cited by its SSRN record only.
