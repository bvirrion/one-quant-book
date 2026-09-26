# 22. Bond and ETF Request-for-Quote Market Making — brief and source ledger

## Brief

- **Hook.** A corporate bond that last traded three weeks ago is on the screen in a request from an asset manager to five dealers; one of them answers in under a second, without a human, because its model has already priced the bond from its neighbours.
- **Sections.** Pricing bonds that do not trade; Auto-quoting request for quote; Win probability and the winner's curse; ETF request for quote and block liquidity; Portfolio trades and all-to-all.
- **Defines.** auto-quoting, win-probability model, cover price.
- **Uses (defined earlier).** request for quote (B2.22), all-to-all trading (B2.22), composite price (B2.22), axe (B2.22), portfolio trade (B2.22), winner's curse (B2.30), hit ratio (B7.23), dealer-to-client platform (B2.4), trade reporting (B2.22), market maker (B1.1), bid--ask spread (B1.1), adverse selection (B1.1), mid price (B1.1), inventory (B2.30).
- **Strategy files.** algorithmic corporate-bond request-for-quote responder; ETF request-for-quote market making; Treasury streaming and request for quote; all-to-all anonymous liquidity provision.
- **Tutorial.** Price synthetic bonds from issuer curves and reported trades, answer simulated requests from clients with private values against competing dealers with firm.rfq, fit a win-probability model and choose the quote that maximises expected profit net of the winner's curse.
- **Build.** `firm.rfqmm`: bond fair price from comparables and stale prints, win-probability model with cover feedback, optimal RFQ response, ETF RFQ pricing from the creation basket; Python, on firm.rfq.
- **Weekend problem.** Five dealers and a bond nobody traded — named result: the auto-quoter's profit per request and win rate at its optimal markup, and how both change with the number of dealers asked.
- **Facts to verify.** MarketAxess and Tradeweb annual reports: automated and portfolio trading volumes (dated); Hendershott and Madhavan 2015 Click or call? (JF); O'Hara and Zhou 2021 The electronic evolution of corporate bond dealers (JFE); FINRA TRACE dissemination rules (dated); Bessembinder, Spatt, Venkataraman 2020 A survey of the microstructure of fixed-income markets (JFQA).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Hendershott and Madhavan (2015): electronic technology to search many bond dealers simultaneously; periodic one-sided electronic auctions viable and important even in inactively traded instruments; a compromise between bilateral search and continuous double auctions | Journal of Finance 70(1), 2015, 419-447 | https://api.crossref.org/works/10.1111/jofi.12164 | 2026-09-25 | Crossref abstract: "periodic one-sided electronic auctions are a viable and important source of liquidity even in inactively traded instruments" | §2; strategy file |
| F2 | O'Hara and Zhou (2021): MarketAxess and TRACE data; electronic RFQ trading fairly small and segmented but with wide-ranging effects on transaction costs and execution quality in electronic, voice and interdealer trading; a market in transition | Journal of Financial Economics 140(2), 2021, 368-390 | https://ideas.repec.org/a/eee/jfinec/v140y2021i2p368-390.html | 2026-09-25 | abstract: "electronic trading remains fairly small and segmented, but has wide-ranging effects on transaction costs and execution quality in both electronic and voice trading, and the interdealer market" | §2; strategy files |
| F3 | MarketAxess FY2025: record revenue $846 million; portfolio trading ADV +48% to record $1.4 billion; block trading ADV +24% to record $5 billion; dealer-initiated ADV +33%; approximately 2,100 firms | MarketAxess Form 8-K Ex. 99.1, 6 Feb 2026 (SEC EDGAR) | https://www.sec.gov/Archives/edgar/data/1278021/000119312526040253/mktx-ex99_1.htm | 2026-09-25 | "Record Revenue of $846 Million in 2025"; "48% Increase in Portfolio Trading ADV to Record $1.4 Billion in 2025"; "24% Increase in Block Trading ADV to Record $5 Billion"; "33% Increase in Dealer-Initiated ADV"; "Approximately 2,100 firms" | dat:hf:bond-and-etf-request-for-quote-market-making:mktx |
| F4 | Joint Staff Report (July 2015): on 15 October 2014, between 9:33 and 9:39 a.m. ET the 10-year yield fell 16 bp, then between 9:39 and 9:45 nearly retraced with no apparent trigger; uncharacteristically shallow depth | Joint Staff Report, The U.S. Treasury Market on October 15, 2014 (SEC copy) | https://www.sec.gov/files/treasury-market-volatility-10-14-2014-joint-report.pdf | 2026-09-25 | pdftotext: "In the six minutes between 9:33 am ET and 9:39 am ET, the 10-year yield decreased 16 basis points. Between 9:39 am ET and 9:45 am ET, the 10-year yield then abruptly reversed course and nearly retraced the latter move, again with no apparent trigger" | strategy file (Treasury) |

## EXCLUDED

- Tradeweb annual volumes; FINRA TRACE dissemination rules; Bessembinder-Spatt-Venkataraman (2020): not fetched, not used.
