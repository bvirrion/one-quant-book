# 18. Autocallables — brief and source ledger

## Brief

- **Hook.** In the first months of 2024 Korean retail investors took large losses on equity-linked securities tied to the Hang Seng China Enterprises Index, sold three years earlier with a knock-in level the index had then seemed unable to reach.
- **Sections.** Payoff anatomy; Pricing: which model; The risk profile: vega, skew, dividends, correlation; Issuer hedging flows; Documented market impact.
- **Defines.** autocallable, autocall trigger, coupon barrier, memory coupon, protection barrier, snowball.
- **Uses (defined earlier).** digital option, barrier shift, gap risk (ch. 15), worst-of option, correlation skew (ch. 17), dividend risk (ch. 5), local volatility (ch. 9), vega, vanna, volga (ch. 4), knock-in option (Book 2 ch. 19), dealer gamma (Book 1 ch. 26).
- **Tutorial.** Price a three-year single-underlying Phoenix autocallable by Monte Carlo under local volatility; compute its vega by expiry bucket and its dividend and skew sensitivities; simulate the issuer's delta-hedge flow as spot falls through the protection barrier.
- **Build.** `firm.autocall`: autocallable term-sheet object and Monte Carlo pricer (single and worst-of, memory, knock-in put) with bucketed Greeks and a hedge-flow simulator.
- **Weekend problem.** The knock-in cliff — named result: the quantity of underlying the issuer sells per 1% fall when spot is 1% above the protection barrier one month before maturity, per 100 million of notes.
- **Facts to verify.** Korean HSCEI-linked ELS 2015-16 episode (Bank of Korea / FSS / BIS); Korean HSCEI ELS losses 2024 (FSS press releases, amounts); Chinese snowball products and the 2024 knock-ins (regulator or quality press); BIS Quarterly Review on autocallable hedging flows; Japanese Nikkei-linked Uridashi notes and hedging flows (BoJ or papers); structured-products market size (industry association data); Natixis 2018 Asian equity-derivatives loss (company release).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | The 2024 "knock-in storm" of snowball products in China: autocallable barrier options with 10%-20% annualised coupons; the CSI 500 and CSI 1000 fell sharply in January 2024, triggering knock-ins set at 70%-80% of initial levels; causes included concentrated maturities and clustered knock-in levels; impacts included institutional hedging pressures | Yin, "Case study on the knock-in storm of snowball products", Journal of Global Economy, Business and Finance 8(3) (2026) 26-33 | https://api.crossref.org/works/10.53469/jgebf.2026.08(03).07 | 2026-09-24 | abstract in Crossref | hook, sec. documented impact |
| F2 | Chinese snowball notes generated predictable, state-dependent dealer hedging flows around knock-in and knock-out barriers; the hedge released across the barrier region grows from about 0.6x notional at twelve months to maturity to about 6x at one month (representative CSI 500-linked note) | Fang, "China's autocallable cycle: dealer hedging flows, market impact, and lessons for Japan's structured-note market", SSRN 7346463 (2026) | https://api.crossref.org/works/10.2139/ssrn.7346463 | 2026-09-24 | abstract in Crossref | sec. issuer hedging flows, sec. documented impact |
| F3 | For an autocallable step-down ELS the issuer's delta increases continually as the underlying approaches the knock-in level, and must be reduced as soon as the knock-in level is touched; the authors propose limiting issuance on the same underlying in view of trading volume | Lim and Choi, "Knock-in and stocks market effect due to ELS issuance and hedging", Journal of Derivatives and Quantitative Studies 23 (2015) 289-321 | https://api.crossref.org/works/10.1108/jdqs-02-2015-b0006 | 2026-09-24 | abstract in Crossref | sec. issuer hedging flows |
| F4 | Losses in Hang Seng China Enterprises Index-linked equity-linked securities are the subject of an empirical pricing study | Kim, Park and Moon, "Markov regime-switching in pricing equity-linked securities: an empirical study for losses in HSCEI-linked products", Finance Research Letters 76 (2025) 106929 | https://api.crossref.org/works/10.1016/j.frl.2025.106929 | 2026-09-24 | Crossref metadata (title) | hook |
| F5 | Guillaume, "Autocallable structured products", Journal of Derivatives 22(3) (2015) 73-94 | Crossref record 10.3905/jod.2015.22.3.073 | https://api.crossref.org/works/10.3905/jod.2015.22.3.073 | 2026-09-24 | Crossref metadata | omsources |
| F6 | HSCEI-linked ELS in Korea: outstanding balance 19.3 trillion won as of 15 November 2023; 10.2 trillion won due to expire in the first half of 2024; losses on products sold by the five commercial banks had reached 229.6 billion won; knock-in usually at 50% of the initial price | KED Global, "Korean investors doomed to suffer $171 mn losses from HSCEI ELS", 22 January 2024 | https://www.kedglobal.com/korean-stock-market/newsView/ked202401220014 | 2026-09-24 | article text (quoted) | hook |

## EXCLUDED

- The 2015-16 HSCEI ELS episode and the FSS's own releases on the 2024 losses: not fetched; the 2024 amounts come from the press report F6 (restored in Phase C once web search was available).
- Natixis's 2018 loss on Asian equity derivatives, structured-products market size, Japanese Uridashi flows, a BIS Quarterly Review on autocallables: no fetchable source; not mentioned.
