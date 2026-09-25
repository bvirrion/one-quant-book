# 9. Flows — brief and source ledger

## Brief

- **Hook.** Mutual funds forced to sell by redemptions push their holdings down for months; a fund-flow signal built from quarterly filings predicts it.
- **Sections.** Flow-driven price pressure; Mutual-fund redemptions and fire sales; ETF and index-fund flows; Quarterly holdings as a signal.
- **Defines.** flow-induced trading, price pressure, 13F holdings.
- **Uses (defined earlier).** fire sale (B3.28), crowding (B7.28), backtest (B7.16), vectorised backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28), fundamental factor model (B7.24).
- **Strategy files.** fire-sale reversal; flow-induced pressure; ETF creation-redemption flow; holdings-overlap signal.
- **Tutorial.** Simulate funds on firm.synthmkt with flows chasing past performance; compute each stock's flow-induced trading from holdings, trade the predicted pressure and its reversal; read the structure of real 13F filings from EDGAR.
- **Build.** `firm.flowpress`: fund holdings and flow simulation, flow-induced trading per stock (Lou 2012), pressure and reversal signals; Python.
- **Weekend problem.** Forced sellers — named result: the price pressure of flow-induced trading and the share that reverses within a year.
- **Facts to verify.** Coval and Stafford 2007, Asset fire sales (JFE); Lou 2012, A flow-based explanation for return predictability (RFS); Ben-David, Franzoni, Moussawi 2018 ETFs and volatility (JF); SEC Form 13F instructions (EDGAR); Gabaix and Koijen 2021 inelastic markets hypothesis (NBER).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | J. Coval, E. Stafford, "Asset fire sales (and purchases) in equity markets", Journal of Financial Economics 86(2) (2007) 479-512 (NBER working paper 11357, 2005): mutual fund transactions caused by flows, 1980-2003; funds with large outflows (inflows) decrease (increase) existing positions, creating price pressure in securities held in common; investors who trade against constrained funds earn significant returns for providing liquidity; future flow-driven transactions are predictable, creating an incentive to front-run | Crossref metadata; NBER abstract | https://doi.org/10.1016/j.jfineco.2006.09.007 ; https://www.nber.org/papers/w11357 | 2026-09-25 | NBER abstract: "Funds experiencing large outflows (inflows) tend to decrease (increase) existing positions, which creates price pressure in the securities held in common by these funds"; "future flow-driven transactions are predictable, creating an incentive to front-run" | section 1; section 2; strat:s1:flows:firesale; strat:s1:flows:pressure; omsources |
| F2 | D. Lou, "A flow-based explanation for return predictability", Review of Financial Studies 25(12) (2012) 3457-3489: flow-induced trading aggregated across mutual funds has a significant, temporary price impact; the expected part of flow-induced trading forecasts stock and fund returns in the following year, reversed in subsequent years; the flow effect can fully account for fund performance persistence and the smart-money effect and partially explain momentum | Crossref metadata; OpenAlex abstract | https://doi.org/10.1093/rfs/hhs103 | 2026-09-25 | abstract: "document a significant, temporary price impact of such uninformed trading"; "the expected part of flow-induced trading positively forecasts stock and mutual fund returns in the following year, which are then reversed in subsequent years" | hook; section 1; tutorial; strat:s1:flows:pressure; omsources |
| F3 | I. Ben-David, F. Franzoni, R. Moussawi, "Do ETFs increase volatility?", Journal of Finance 73(6) (2018) 2471-2535: liquidity shocks in ETFs propagate to their baskets through arbitrage; stocks with higher ETF ownership have significantly higher volatility and more negative autocorrelation; they earn a risk premium of up to 56 basis points a month | Crossref metadata; OpenAlex abstract | https://doi.org/10.1111/jofi.12727 | 2026-09-25 | abstract: "stocks with higher ETF ownership display significantly higher volatility"; "ETF ownership increases the negative autocorrelation in stock prices" | section 3; strat:s1:flows:etf; omsources |
| F4 | X. Gabaix, R. S. J. Koijen, "In search of the origins of financial fluctuations: the inelastic markets hypothesis", NBER working paper 28967 (2021): institutions are fairly constrained, so the aggregate stock market's price elasticity of demand is small; investing $1 in the stock market increases its aggregate value by about $5 | NBER abstract | https://www.nber.org/papers/w28967 | 2026-09-25 | abstract: "investing $1 in the stock market increases the market's aggregate value by about $5" | section 1; omsources |
| F5 | SEC, Frequently Asked Questions about Form 13F: institutional investment managers exercising investment discretion over $100 million or more in Section 13(f) securities must file Form 13F; filings are due within 45 days after the end of each calendar quarter; the Official List of Section 13(f) Securities is published shortly after each quarter's end | SEC staff FAQ page | https://www.sec.gov/rules-regulations/staff-guidance/division-investment-management-frequently-asked-questions/frequently-asked-questions-about-form-13f | 2026-09-25 | "exercise investment discretion over $100 million or more in Section 13(f) securities must file Form 13F"; "The filing is due within 45 days after December 31" | dat:s1:flows:13f; section 4 |

## EXCLUDED

- Any named fund's 13F holdings: not used; the chapter describes the filing, not a filer.
- Real fund-flow data (monthly assets and flows by fund): commercial; the chapter's funds are simulated.
- The price-impact parameter of the chapter's funds (1.5 per unit of flow-induced trading) is the chapter's own choice, not an estimate from the literature.

