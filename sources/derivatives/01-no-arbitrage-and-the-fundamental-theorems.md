# 1. No Arbitrage and the Fundamental Theorems — brief and source ledger

## Brief

- **Hook.** Four S&P 500 index options, two calls and two puts, bought and sold together, pay exactly the distance between two strikes at expiry whatever the index does; their price on the screen is a zero-coupon bond, and a desk reads an interest rate off it.
- **Sections.** Arbitrage and the law of one price; State prices in one period; Martingale measures and the first fundamental theorem; Completeness, replication and the second theorem; Price bounds when the market is incomplete.
- **Defines.** arbitrage, law of one price, contingent claim, replicating portfolio, self-financing strategy, Arrow--Debreu security, state price, state-price density, fundamental theorem of asset pricing, complete market, super-replication price, box spread.
- **Uses (defined earlier).** call option, put option, strike price, expiry, European exercise (Book 1 ch. 23), put--call parity (Book 1 ch. 25), martingale, filtration, change of measure (Book 4 ch. 1), equivalent martingale measure, risk-neutral measure (Book 4 ch. 5), numeraire (Book 4 ch. 5), zero-coupon rate (Book 2 ch. 3), overnight benchmark rate (Book 2 ch. 1), repo rate (Book 2 ch. 5).
- **Tutorial.** From a table of traded payoffs on a finite state grid, solve for the state prices; when no positive solution exists, find the arbitrage portfolio (a small hand-written simplex in numpy, no solver library); read the financing rate off a box spread.
- **Build.** `firm.arbcheck`: static-arbitrage checker for a chain of European quotes (bounds, monotonicity and convexity in strike, parity, box bounds); returns the violated inequality and the portfolio that exploits it.
- **Weekend problem.** The box-spread rate — named result: the annualised financing rate implied by an index box spread and its spread over the overnight benchmark rate.
- **Facts to verify.** Cboe SPX options: European, cash-settled, multiplier (reuse Book 1 ledger); box spreads used as a financing instrument (Cboe materials); box-spread implied rates versus Treasury rates (van Binsbergen, Diamond, Grotteria 2022, JFE); Harrison-Kreps 1979, Harrison-Pliska 1981, Delbaen-Schachermayer 1994 publication details; Arrow 1953/1964 and Debreu 1959 state-contingent claims.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Index box spreads: USD 929 million average daily notional volume in 2024; standardised 1,000-point strike distances, USD 100,000 notional; rates typically 10-55 bp above three-month Treasury yields | Cboe, SPX Box Spreads white paper landing page | https://go.cboe.com/download-cboe-spx-box-spread-whitepaper | 2026-09-24 | "$929 million in average daily notional volume in 2024"; "typically 10-55 basis points above three-month U.S. Treasury yields"; "1,000-point strike distances creating a highly liquid standardized $100,000 notional order size" | dat:dv:no-arbitrage-and-the-fundamental-theorems:box |
| F2 | A box lends when bought and borrows when sold; the payoff is the strike distance; the counterparty is the options clearing house (OCC) | Cboe Insights, "Why consider box spreads as an alternative borrowing and lending strategy", 16 Oct 2024 | https://www.cboe.com/insights/posts/why-consider-box-spreads-as-an-alternative-borrowing-lending-strategy/ | 2026-09-24 | "you are left with a guaranteed payoff of the spread in strikes between the synthetic long position and the synthetic short position" | hook; def box; dat box |
| F3 | SPX options: European, cash-settled, USD 100 multiplier | Book 1 ledger, ch. 25 F4 (Cboe SPX specifications) | https://www.cboe.com/tradable_products/sp_500/spx_options/specifications/ | 2026-09-18 | reused row | hook; problem |
| F4 | Box-spread implied rates recover riskless rates; the Treasury convenience yield is about 40 bp, larger below three months; published JFE 143(1) 2022, 1-29 | van Binsbergen, Diamond, Grotteria, "Risk-free interest rates" (NBER w26138; JFE 2022) | https://www.nber.org/papers/w26138 | 2026-09-24 | "The convenience yield on treasuries equals about 40 basis points, is larger below 3 months maturity" | problem q15; omsources |
| F5 | Harrison and Kreps (1979), JET 20(3), 381-408 | IDEAS/RePEc record | https://ideas.repec.org/a/eee/jetheo/v20y1979i3p381-408.html | 2026-09-24 | bibliographic record | §3; omsources |
| F6 | Harrison and Pliska (1981), SPA 11, 215-260: completeness iff martingale representation | EconPapers record | https://econpapers.repec.org/RePEc:eee:spapps:v:11:y:1981:i:3:p:215-260 | 2026-09-24 | "the security market is complete if and only if its vector price process has a certain martingale representation property" | §3-4; omsources |
| F7 | Delbaen and Schachermayer (1994), Math. Annalen 300, 463-520: FTAP in continuous time, NFLVR | Springer record | https://link.springer.com/article/10.1007/BF01450498 | 2026-09-24 | bibliographic record | §3; omsources |
| F8 | Arrow, "The role of securities in the optimal allocation of risk-bearing", RES 31(2) (1964) 91-96, translated from the 1953 French original | IDEAS/RePEc record | https://ideas.repec.org/a/oup/restud/v31y1964i2p91-96..html | 2026-09-24 | bibliographic record | §2; omsources |
| F9 | Dalang, Morton, Willinger (1990), Stochastics and Stochastics Reports 29(2) 185-201: FTAP in finite discrete time on an arbitrary probability space | EPFL Infoscience record | https://infoscience.epfl.ch/record/129915?of=HB | 2026-09-24 | "the absence of arbitrage opportunities characterizes the existence of an equivalent martingale measure" (search summary of the record) | §3 |

## EXCLUDED

- Retail box-spread losses on American single-stock options (press stories): not used; the text states the mechanism (early assignment) only.
