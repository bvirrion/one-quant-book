# 13. Index and Basket Arbitrage — brief and source ledger

## Brief

- **Hook.** The index future ticks up and five hundred stocks have not moved yet; buying all five hundred takes longer than the gap lasts, so the arbitrageur buys the thirty that matter and accepts the risk of the rest.
- **Sections.** The futures--cash basis at high frequency; Partial baskets and tracking risk; Legging and execution risk; Financing and dividend risk; The same index on several futures.
- **Defines.** partial basket, legging risk, cross-listed futures.
- **Uses (defined earlier).** index arbitrage (B9.26), fair value (B1.21), implied financing rate (B1.21), basis (B1.21), mini contract (B1.22), micro contract (B1.22), dividend risk (B5.5), law of one price (B5.1), transaction cost analysis (B7.23), implementation shortfall (B7.19).
- **Strategy files.** futures against an optimised partial basket; cross-listed index futures arbitrage; mini against full-size contract arbitrage.
- **Tutorial.** On a synthetic index of fifty names driven by a factor, with the future leading the stocks by a planted lag, choose partial baskets of five to fifty names, trade the basis with execution lags, and measure tracking error, legging losses and net capture.
- **Build.** `firm.basketarb`: partial-basket selection by tracking-error minimisation, basis bands with financing and dividends, legging simulation with per-leg latency, cross-listed contract spreads with currency and hours; Python.
- **Weekend problem.** Thirty names out of five hundred — named result: the net edge per trade as a function of the basket size, and the size that maximises it.
- **Facts to verify.** MacKinlay and Ramaswamy 1988 Index-futures arbitrage and the behavior of stock index futures prices (RFS); Roll, Schwartz, Subrahmanyam 2007 Liquidity and the law of one price: the futures-cash basis (JF); Nikkei 225 futures listings on OSE, SGX and CME (dated); CME Micro E-mini launch and contract specification (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Roll, Schwartz, Subrahmanyam (2007): NYSE Composite index futures basis and aggregate NYSE liquidity over about 3,000 trading days; liquidity and the basis forecast each other and are contemporaneously correlated; two-way Granger causality between short-term absolute basis and liquidity; basis shocks predict future liquidity | Journal of Finance 62(5), 2007, 2201-2234 | https://www.anderson.ucla.edu/documents/areas/fac/finance/one_price.pdf | 2026-09-25 | abstract (pdftotext): "Liquidity and the basis forecast each other in addition to being contemporaneously correlated. There is evidence of two-way Granger causality between the short-term absolute basis and liquidity"; "3000 trading days" (search abstract) | §1; strategy file |
| F2 | CME Group launched Micro E-mini futures on the S&P 500, Nasdaq-100, Russell 2000 and DJIA on 6 May 2019, one-tenth the size of E-mini futures | CME Group press release via PR Newswire, 6 May 2019 | https://www.prnewswire.com/news-releases/cme-group-announces-launch-of-new-micro-e-mini-equity-index-futures-300843857.html | 2026-09-25 | "Micro E-mini futures on the S&P 500, Nasdaq-100, Russell 2000 and Dow Jones Industrial Average indexes...became available for trading today"; "one-tenth the size of CME Group's existing E-mini equity index futures" | dat:hf:index-and-basket-arbitrage:listings |
| F3 | Nikkei 225 futures: SGX and CME JPY 500 x index (USD or JPY), tick 5 points; OSE JPY 1,000 x index, JPY only, tick 10 points; CME-SGX mutual offset system | Phillip Nova (broker), "Differences between the Nikkei 225 futures contracts on SGX, CME Group and OSE", 5 June 2024 | https://www.phillipnova.com.sg/market_trends/differences-between-the-nikkei-225-futures-contracts-on-sgx-cme-group-and-ose/ | 2026-09-25 | "¥500 multiplied by the index futures price"; "5 index points or ¥2,500 per contract"; OSE "¥1,000 multiplied by the index", "10 index points"; MOS "allows traders ... to take positions at either exchange and clear them at the other on the same trading day" | dat:hf:index-and-basket-arbitrage:listings |

## EXCLUDED

- MacKinlay and Ramaswamy (1988): abstract not retrievable (publisher page behind a bot check, no open copy); not cited.
- The $5-a-point dollar Nikkei multiplier used in the hedge-ratio example is illustrative (the fetched comparison gives the CME contract as JPY 500 x index in USD or JPY); the text states it as an example, not as a contract term.
- Exchange pages (JPX, cmegroup.com) returned 403 or timed out; contract terms taken from the broker comparison above.
