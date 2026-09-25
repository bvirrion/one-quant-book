# 11. Merger Arbitrage — brief and source ledger

## Brief

- **Hook.** A cash deal at forty dollars trades at 38.60: a 3.6 per cent spread that pays unless the deal breaks, in which case the target falls back to thirty. The spread is an insurance premium against a break.
- **Sections.** Deal spreads and their pricing; Break risk and its correlation with the market; Stock deals and collars; Regulatory and financing risk; Portfolio of deals.
- **Defines.** merger arbitrage, tender offer, deal spread, break price, stock-deal collar, implied deal probability.
- **Uses (defined earlier).** short sale (B1.6), backtest (B7.16), vectorised backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28), fundamental factor model (B7.24).
- **Strategy files.** cash-deal spread; stock-for-stock hedged spread; collar deals; diversified deal portfolio.
- **Tutorial.** Price deal spreads with a completion probability and a break price, simulate a portfolio of deals whose breaks cluster in market downturns, and measure its payoff against the market (a short put, as the literature found).
- **Build.** `firm.mergerarb`: deal-spread model (cash, stock and collar terms, implied completion probability), deal portfolio simulation with market-dependent breaks; Python.
- **Weekend problem.** Selling insurance — named result: the portfolio's beta in down and up markets and its implied completion probability against realised completion.
- **Facts to verify.** Mitchell and Pulvino 2001, Characteristics of risk and return in risk arbitrage (JF); Baker and Savasoglu 2002 limited arbitrage in mergers and acquisitions (JFE); Hart-Scott-Rodino waiting period (FTC, dated); a documented broken deal from public filings (SEC EDGAR).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | M. Mitchell, T. Pulvino, "Characteristics of risk and return in risk arbitrage", Journal of Finance 56(6) (2001) 2135-2175: 4,750 mergers from 1963 to 1998; risk arbitrage returns are positively correlated with market returns in severely depreciating markets but uncorrelated in flat and appreciating markets, similar to selling uncovered index put options; after transaction costs and a contingent-claims control for the nonlinearity, excess returns of four percent a year | Crossref metadata; OpenAlex abstract | https://doi.org/10.1111/0022-1082.00401 | 2026-09-25 | abstract: "risk arbitrage returns are positively correlated with market returns in severely depreciating markets but uncorrelated with market returns in flat and appreciating markets"; "similar to those obtained from selling uncovered index put options"; "risk arbitrage generates excess returns of four percent per year" | hook; section 2; section 5; strat:s1:merger-arbitrage:cash; strat:s1:merger-arbitrage:portfolio; omsources |
| F2 | M. Baker, S. Savasoglu, "Limited arbitrage in mergers and acquisitions", Journal of Financial Economics 64(1) (2002) 91-115 | Crossref metadata | https://doi.org/10.1016/s0304-405x(02)00072-7 | 2026-09-25 | Crossref: authors, title, journal, volume, issue, pages, year | section 5; omsources |
| F3 | FTC, Premerger Notification and the Merger Review Process: once the filing is complete, parties must wait 30 days (15 days for a cash tender offer or a bankruptcy) or until the agencies grant early termination before consummating the deal; the reviewing agency can grant early termination, let the waiting period expire, or issue a Second Request | FTC guidance page | https://www.ftc.gov/advice-guidance/competition-guidance/guide-antitrust-laws/mergers/premerger-notification-merger-review-process | 2026-09-25 | "the parties must wait 30 days (15 days in the case of a cash tender offer or a bankruptcy) or until the agencies grant early termination of the waiting period before they can consummate the deal"; "issue a Request for Additional Information ('Second Request')" | dat:s1:merger-arbitrage:hsr; section 4 |

## EXCLUDED

- A documented broken deal from EDGAR filings: not included; no firm is named.
- Baker and Savasoglu (2002), content: abstract not retrieved (NBER lookup returned another paper); cited without quoting results.
- Merger-arbitrage fund or index returns: no primary source fetched.

