# 20. Options: Cross-Venue and Volatility Arbitrage at Speed — brief and source ledger

## Brief

- **Hook.** The day before a stock goes ex-dividend, thousands of deep in-the-money calls should be exercised and some are not; the holders who forget pay the ones who remember, and the trade that collects it has been in the exchanges' rulebooks for years.
- **Sections.** Parity at speed: conversions and reversals; Box spreads and the rate they imply; Early exercise, dividends and the dividend play; The same volatility on several listings.
- **Defines.** conversion arbitrage, reversal arbitrage, jelly roll.
- **Uses (defined earlier).** put--call parity (B1.25), box spread (B5.1), dividend play (B5.26), early-exercise premium (B5.6), American exercise (B1.23), assignment (B1.23), implied borrow rate (B5.5), live surface fit (ch19), law of one price (B5.1), transaction cost analysis (B7.23), implementation shortfall (B7.19).
- **Strategy files.** conversion and reversal arbitrage; box-spread financing arbitrage; dividend play on unexercised calls; index against ETF options volatility arbitrage.
- **Tutorial.** Scan synthetic option chains on several listings for parity, box and early-exercise violations with firm.parity and firm.american, net them of fees, borrow and assignment risk, and measure how many survive a one-tick execution lag.
- **Build.** `firm.optarb`: parity, box and jelly-roll scanners with borrow and rates, the dividend-play assignment model, cross-listing volatility spreads; Python, on firm.parity and firm.american.
- **Weekend problem.** The calls nobody exercised — named result: the dividend play's expected profit per contract as a function of the share of holders who fail to exercise.
- **Facts to verify.** Pool, Stoll, Whaley 2008 Failure to exercise call options (JFM); Hao, Kalay, Mayhew 2010 Ex-dividend arbitrage in option markets (RFS); van Binsbergen, Diamond, Grotteria 2022 Risk-free interest rates (JFE); Ofek, Richardson, Whitelaw 2004 Limited arbitrage and short sales restrictions (JFE); Exchange fee caps or rules on dividend strategies (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Pool, Stoll and Whaley: calls on stocks with quarterly dividends >= 1 cent, Jan 1996-Apr 2006; more than half of outstanding long positions go unexercised when exercise is optimal; holders lost over $491 million over ten years; market makers capture the lion's share with a dividend spread strategy | Journal of Financial Markets 11(1), 2008, 1-35 (abstract of the SSRN version, 10.2139/ssrn.972613) | https://api.crossref.org/works/10.2139/ssrn.972613 | 2026-09-25 | "we find that more than half of outstanding long positions go unexercised"; "caused call option holders to lose over $491 million over a ten-year period"; "market makers capture the lion's share of the proceeds" | hook; §3; strategy file |
| F2 | Hao, Kalay and Mayhew: a significant fraction of open interest remains unexercised on ex-dividend; a trading scheme lets short-term traders receive a significant fraction of the gains; it inflates reported volume; facilitated by exchanges' limitations on transaction costs | Review of Financial Studies 23(1), 2010, 271-303 (abstract of the SSRN version, 10.2139/ssrn.931777) | https://api.crossref.org/works/10.2139/ssrn.931777 | 2026-09-25 | "The trading scheme inflates reported volume and distorts its traditional relations to liquidity"; "facilitated by limitations on transaction costs passed by the various option exchanges" | §3; strategy file |
| F3 | van Binsbergen, Diamond and Grotteria: risk-free rates inferred from risky asset (option) prices without a model of risk; Treasury convenience yield about 40 bp, larger below 3 months, quadruples in the financial crisis | Journal of Financial Economics 143(1), 2022, 1-29 (NBER w26138 abstract) | https://www.nber.org/papers/w26138 | 2026-09-25 | "The convenience yield on treasuries equals about 40 basis points, is larger below 3 months maturity, and quadruples during the financial crisis" | §2; strategy file |

## EXCLUDED

- Ofek, Richardson and Whitelaw (2004): not fetched; not used.
- Exchange fee caps on dividend strategies: not fetched; described only through Hao, Kalay and Mayhew's finding.
