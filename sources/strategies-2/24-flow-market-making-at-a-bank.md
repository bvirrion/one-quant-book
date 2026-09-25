# 24. Flow Market Making at a Bank — brief and source ledger

## Brief

- **Hook.** A bank's flow desk makes money by pricing clients, not by predicting prices: it knows which clients' trades will move against it and charges them accordingly.
- **Sections.** The franchise and its P&L; Axes and skewing; Client tiering; Internalisation.
- **Defines.** client tiering, axe-driven skew, franchise P&L.
- **Uses (defined earlier).** axe (B2.22), franchise (B1.2), internalisation (B1.10), quote skewing (B2.15), mark-out curve (B7.23), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** tiered pricing by client mark-out; axe skewing; internalisation before hedging; RFQ win-rate management.
- **Tutorial.** Simulate a bank desk facing clients with different information, price them by tier from their mark-outs, skew quotes to axes and internalise opposite flows, and decompose the franchise P&L.
- **Build.** `firm.flowmm`: client mark-out estimation, tiered pricing, axe skewing and an internalisation engine with P&L decomposition; Python.
- **Weekend problem.** Pricing the client — named result: the desk's spread capture by tier and the share of risk internalised.
- **Facts to verify.** Bjonnes and Rime or Butz and Oomen 2019 internalisation by electronic FX spot dealers (Quantitative Finance); Oomen 2017 last look (Quantitative Finance).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | M. Butz, R. Oomen, "Internalisation by electronic FX spot dealers", Quantitative Finance 19(1) (2019; online 2018) 35-56: dealers either internalise a customer's trade (warehouse the risk awaiting offsetting flow) or externalise it (hedge in the open market); a queuing model gives closed-form internalisation horizons; with BIS triennial survey data a representative tier-1 dealer takes several minutes on average to internalise a trade in the most liquid currencies, tens of minutes in emerging markets; internalisation costs are lower for dealers willing to hold more risk and facing more price-sensitive traders; customers should distinguish externalisers and passive and aggressive internalisers | Crossref metadata; OpenAlex abstract | https://doi.org/10.1080/14697688.2018.1504167 | 2026-09-25 | abstract: "a representative tier 1 dealer takes on average several minutes to complete the internalisation of a customer's trade in the most liquid currencies, increasing to tens of minutes for emerging markets" | hook; section 4; strat:s2:flow-market-making-at-a-bank:internalise; exercise 6; solutions; omsources |
| F2 | R. Oomen, "Last look", Quantitative Finance 17(7) (2017) 1057-1070: last look decides whether, and at what rate, a liquidity provider accepts a deal request after latency; the design and protocol determine execution risk but need not affect effective transaction costs; when a trader adversely selects the liquidity provider, the distinction between symmetric and asymmetric designs fades and the protocol drives execution risk | Crossref metadata; OpenAlex abstract | https://doi.org/10.1080/14697688.2016.1262545 | 2026-09-25 | abstract: "the choice of last look design and trading protocol determines the degree of execution risk inherent in the process, but the effective transaction costs borne by the trader need not be affected by it" | section 3; solutions; omsources |
| F3 | R. Oomen, "Price signatures", Quantitative Finance 19(5) (2019) 733-761: price signatures measure systematic price dynamics around executions (a curve, not a point); functional data analysis with bootstrap inference; applied to live OTC currency trading, they distinguish internalising from externalising liquidity providers | Crossref metadata; OpenAlex abstract | https://doi.org/10.1080/14697688.2018.1532102 | 2026-09-25 | abstract: "functional data analysis of price signatures can be used to distinguish between internalising and externalising liquidity providers" | section 3; strat:s2:flow-market-making-at-a-bank:tier; solutions; omsources |

## EXCLUDED

- Bank flow-desk P&L, spreads by client tier and internalisation ratios of named dealers: not public; the desk and its clients are synthetic (planted: 60/20/10 clients with post-trade drifts of 0, 0.8 and 2.5 bp, competing quotes drawn per client).
- Bjonnes and Rime on dealer behaviour: SSRN versions only found, not the journal article; not cited.
- Named banks' flow businesses: no citable primary source; no firm named.
