# 26. Zero-Day Options, Weeklies and Retail Options Flow — brief and source ledger

## Brief

- **Hook.** By mid-afternoon the most traded option in the world expires in two hours.
- **Sections.** From monthlies to dailies; Who trades short-dated options; Gamma near expiry; Dealer hedging and the underlying; Retail options flow.
- **Defines.** zero-day option, weekly option, gamma, delta hedging, dealer gamma, pin risk.
- **Tutorial.** Gamma of an at-the-money option as expiry approaches; hedging flow for a price move.
- **Build.** Gamma-exposure estimator.
- **Weekend problem.** The last hour — named result: shares to trade per 1% move.
- **Facts to verify.** 0DTE share of SPX volume (Cboe); SPX daily expiries since 2022; retail share of options volume (Cboe/OCC).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | SPX 0DTE options averaged 2.3 million contracts daily in 2025, 59% of total SPX volume; total US options volume topped 15.2 billion contracts in 2025, 26% above 2024 | Cboe, The State of the Options Industry: 2025 | https://www.cboe.com/insights/posts/the-state-of-the-options-industry-2025 | 2026-09-18 | "averaged 2.3 million contracts daily, or 59%"; "topped 15.2 billion contracts in 2025, 26% above 2024" | hook; dat:m1:zero-day-options-and-retail-flow:dailies; exo 5 |
| F2 | SPX Weeklys: Tuesday expirations from 18 April 2022 and Thursday expirations from 11 May 2022, giving an expiry every trading day | Cboe press release, 13 April 2022 (search excerpt) | https://ir.cboe.com/news/news-details/2022/Cboe-to-Add-Tuesday-and-Thursday-Expirations-for-SPX-Weeklys-Options-04-13-2022/default.aspx | 2026-09-18 | "Tuesday expirations beginning Monday, April 18, 2022, and Thursday expirations beginning Wednesday, May 11, 2022" | dat dailies |

## EXCLUDED

- Dates of the first Friday, Monday and Wednesday SPX Weeklys: not verified; the dated box gives only their order.
- Retail share of options volume and of 0DTE volume: figures circulate (Cboe, brokers), none fetched; the section is qualitative.
- Cboe's research claim that customer 0DTE flow is balanced and dealers' net gamma small: not fetched; the text says "often two-sided" and presents it as the reason to measure rather than assume.
- 0DTE share of all US listed options (24.1% in 2025): search excerpt from a trade publication only; not printed.
- "About \$5 million" premium in the problem: computed from the chapter's own 0.8 sigma sqrt(T) approximation at the open (0.4% of \$1.2bn); it is the problem's arithmetic, not a market fact.
