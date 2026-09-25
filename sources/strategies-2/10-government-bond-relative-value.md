# 10. Government-Bond Relative Value — brief and source ledger

## Brief

- **Hook.** Fit a smooth curve to a government's bonds and some sit above it and some below; a relative-value book buys the cheap and sells the rich, hedged, and waits a few weeks for the curve to take them back.
- **Sections.** Fitted curves and their residuals; Butterflies and curve trades; Rich-cheap signals and their decay; Leverage and funding.
- **Defines.** fitted-curve residual, rich-cheap signal, duration-neutral butterfly.
- **Uses (defined earlier).** DV01 (B2.3), zero-coupon rate (B2.3), repo rate (B2.5), on-the-run (B2.4), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** fitted-curve rich-cheap; duration-neutral butterfly; curve steepener or flattener; off-the-run versus on-the-run; principal-component-hedged residual.
- **Tutorial.** Simulate a government curve with three factors and bond-specific pricing errors that revert, fit a smooth curve each day, and trade residuals hedged in duration and in principal components.
- **Build.** `firm.bondrv`: synthetic government bond market, daily curve fitting (Nelson-Siegel-Svensson or splines), residuals, PCA hedges and a rich-cheap book; Python.
- **Weekend problem.** Above and below the curve — named result: the rich-cheap book's Sharpe ratio by hedge and the half-life of the residuals.
- **Facts to verify.** Gurkaynak, Sack, Wright 2007 the U.S. Treasury yield curve: 1961 to the present (J. Monetary Economics); Duarte, Longstaff, Yu 2007 (as ch9); Fed H.15 or FRED yields (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | R. S. Gurkaynak, B. Sack, J. H. Wright, "The U.S. Treasury yield curve: 1961 to the present", Journal of Monetary Economics 54(8) (2007) 2291-2304 (FEDS 2006-28): the Federal Reserve Board's daily Treasury yield curve estimates from 1961, made public; a Svensson (1994) extension of Nelson-Siegel; the fit excludes securities with option-like features, securities with less than three months to maturity, all bills (segmented markets), twenty-year bonds from 1996 (often cheap relative to ten-year notes), and the on-the-run and first off-the-run issues at two to thirty years, which often trade at a premium owing to liquidity and repo specialness | Crossref metadata; RePEc/OpenAlex abstract; FEDS working paper PDF (pdftotext) | https://doi.org/10.1016/j.jmoneco.2007.06.029 ; https://www.federalreserve.gov/pubs/feds/2006/200628/200628pap.pdf | 2026-09-25 | "We employ the Svensson methodology for estimating our benchmark yield curve"; "(v) We exclude the two most recently issued securities ... These are the 'on-the-run' and 'first off-the-run' issues that often trade at a premium to other Treasury securities, owing to their greater liquidity and their frequent specialness in the repo market" | section 1; strat:s2:government-bond-relative-value:otr; omsources |
| F2 | J. Duarte, F. A. Longstaff, F. Yu (2007), as in chapter 9: strategies requiring more intellectual capital earned significant alphas; many fixed-income arbitrage strategies have positively skewed returns | Crossref metadata; OpenAlex abstract | https://doi.org/10.1093/rfs/hhl026 | 2026-09-25 | as chapter 9 ledger F2 | section 3 |
| F3 | Board of Governors H.15 constant-maturity Treasury yields via FRED (DGS1, DGS2, DGS3, DGS5, DGS7, DGS10, DGS20), 3 January 1994 to 23 September 2026, used only through derived statistics | FRED series pages (CSV download) | https://fred.stlouisfed.org/series/DGS10 (and DGS1 ... DGS20) | 2026-09-25 | files downloaded; statistics recomputed by s2_fetch_ust.py | section 1; section 2 |

## EXCLUDED

- Individual Treasury bond prices and fitted residuals: no free daily source; the chapter's rich-cheap book is synthetic.
- Repo haircuts and leverage of relative-value funds: no source fetched; the leverage section states mechanisms only.
- The synthetic error sizes (2 bp fast, 2 bp slow, 0.5 bp quote noise) and the cost of 0.25 bp per DV01 are the chapter's own choices.

