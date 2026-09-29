# 10. Crypto-Native Firms — brief and source ledger

## Brief

- **Hook.** The largest US-listed crypto exchange cut its staff by about a fifth in June 2022 and again in January 2023, then hired back as prices rose: in crypto, headcount follows the price of the asset the industry trades. (Verify against the firm's filings and releases.)
- **Sections.** Kinds of employer: market makers, funds, exchanges, protocol teams and foundations; What is different: round-the-clock operations, custody, token pay, regulatory status; Headcount through the cycle; Paid in tokens; When the firm fails: the employee in the bankruptcy record.
- **Defines.** protocol foundation, token compensation, token warrant.
- **Uses (defined earlier).** centralised exchange (B3.15), token (B3.14), token unlock (B3.24), token market-making agreement (B3.24), crypto-asset service provider (B3.24), Markets in Crypto-Assets Regulation (B3.24), hot wallet (B3.24), stablecoin (B3.14), vesting schedule (B16.10), follow-the-sun trading (B3.29).
- **Tutorial.** Headcount against the cycle: employees and stock-based compensation of listed crypto firms from their 10-Ks and releases against the annual mean of the bitcoin price (a public-domain or openly licensed price series as derived statistics); then value a token grant with firm.tokencomp. End state: a chart of headcount changes against price changes and the distribution of a four-year token grant's value.
- **Build.** `firm.tokencomp`: token-grant valuation (vesting with cliff, lock-up, lognormal price paths at a stated volatility, a liquidity discount, tax at vesting against tax at sale as parameters), with the probability that tax due at vesting exceeds the value at sale; Python; wraps firm.tokenloan's option pricing where it fits.
- **Weekend problem.** Paid in tokens -- named result: the median and 10th-90th percentile value of a four-year token grant with a one-year cliff at 80 per cent volatility against the same nominal in cash, and the probability that tax at vesting exceeds the proceeds.
- **Facts to verify.** Coinbase Global Forms 10-K 2020-2025 and 8-K releases: headcount, layoffs of June 2022 and January 2023 (dated); other listed crypto employers' headcounts (Galaxy Digital, Bakkt or others with filings) (dated); FTX Trading Ltd. chapter 11 docket: treatment of employee claims (court record; neutral with outcome); IRS Rev. Rul. 2023-14 and Notice 2014-21 on tokens received for services; HMRC Cryptoassets Manual on employment income (dated); Electric Capital developer report: monthly active developers (dated, publisher named); Ethereum Foundation or another protocol foundation's own published description of its role.
- **Data.** data/industry/crypto_headcount.csv (derived); price series as derived annual statistics.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Coinbase, Form 10-K for 2022: 'As of December 31, 2022, we had 4,510 employees'; 'In June 2022, the Company announced and completed a restructuring impacting approximately 18% of the Company's headcount ... approximately 1,100 employees in various departments and locations were terminated'; total revenue ($ thousands) 3,194,208 (2022), 7,839,444 (2021), 1,277,481 (2020) | Coinbase Global, Inc., Form 10-K for 2022 | https://www.sec.gov/Archives/edgar/data/1679788/000167978823000031/coin-20221231.htm | 2026-09-29 | sentences quoted | data/industry/crypto_headcount.csv; dat:in:crypto-native-firms:coinbase |
| F2 | Coinbase, Form 10-K for 2023: 'As of December 31, 2023, we had 3,416 employees'; 'In January 2023, the Company announced and completed a restructuring impacting approximately 21% of the Company's headcount as of December 31, 2022 ... approximately 950 employees ... were terminated'; total revenue 3,108,383 ($ thousands) | Coinbase Global, Inc., Form 10-K for 2023 | https://www.sec.gov/Archives/edgar/data/1679788/000167978824000022/coin-20231231.htm | 2026-09-29 | sentences quoted | data; dated box |
| F3 | Coinbase, Form 10-K for 2024: 'As of December 31, 2024, we had 3,772 employees'; total revenue 6,564,028 ($ thousands) | Coinbase Global, Inc., Form 10-K for 2024 | https://www.sec.gov/Archives/edgar/data/1679788/000167978825000022/coin-20241231.htm | 2026-09-29 | sentence quoted | data; dated box |
| F4 | Coinbase, Form 10-K for 2025: 'As of December 31, 2025, we had 4,951 employees'; total revenue 7,181,325 ($ thousands) | Coinbase Global, Inc., Form 10-K for 2025 | https://www.sec.gov/Archives/edgar/data/1679788/000167978826000015/coin-20251231.htm | 2026-09-29 | sentence quoted | data; dated box |
| F5 | IRS Notice 2014-21, Q-11: 'Does virtual currency paid by an employer as remuneration for services constitute wages for employment tax purposes? A-11: Yes.' | US Internal Revenue Service, Notice 2014-21 | https://www.irs.gov/pub/irs-drop/n-14-21.pdf | 2026-09-29 | Q-11/A-11 quoted | section 4 |
| F6 | HMRC Cryptoassets Manual CRYPTO21100: 'Cryptoassets received as employment income count as money's worth ... and are subject to Income Tax and National Insurance contributions on the value of the asset' | HM Revenue & Customs, Cryptoassets Manual, CRYPTO21100 | https://www.gov.uk/hmrc-internal-manuals/cryptoassets-manual/crypto21100 | 2026-09-29 | sentence quoted | section 4 |
| F7 | Ethereum Foundation: 'The Ethereum Foundation (EF) is a non-profit that supports the Ethereum ecosystem'; 'We are not a tech company, or a normal non-profit'; treasury policy: 'periodically selling ETH to ensure sufficient savings for future years, and programmatically increasing our fiat savings in bull markets to fund spending in bear markets' | Ethereum Foundation, home page and EF Report 2024 | https://ethereum.foundation/ef ; https://ethereum.foundation/report-2024.pdf | 2026-09-29 | sentences quoted | definition; section 1 |
| F8 | 11 U.S.C. 507(a)(4): priority for allowed unsecured claims for wages, salaries or commissions earned within 180 days before the petition, up to a per-individual amount; adjusted from $15,150 to $17,150 by notice of 30 January 2025, effective 1 April 2025 | US Code, title 11, section 507 (Cornell LII) and its note on adjustment of dollar amounts | https://www.law.cornell.edu/uscode/text/11/507 | 2026-09-29 | text and note quoted | section 5 |

## EXCLUDED

- Crypto price series: not used (licensing of free series unclear; FRED unreachable); the exchange's own revenue is the cycle proxy.
- FTX employee claims in the chapter 11 docket: not fetched; the priority rule for wage claims is stated from the US Code.
- Developer counts (Electric Capital): not fetched.
- Other listed crypto employers' headcounts: not fetched.

