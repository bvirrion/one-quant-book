# 19. Automated Options Market Making — brief and source ledger

## Brief

- **Hook.** An options market maker quotes every strike and expiry of a stock at once, several thousand prices on a dozen exchanges, and a sweep can hit forty of them in the same millisecond; the exchange's quote protection is what stops the forty-first.
- **Sections.** The live surface; Mass quoting and quote protection; Delta hedging at speed; Per-strike and per-expiry risk; What the major firms have published.
- **Defines.** mass quote, live surface fit, strike risk limit.
- **Uses (defined earlier).** theoretical value (B5.26), vega bucket (B5.26), hedging band (B5.26), quote protection (B1.24), options market maker (B1.24), quoting obligation (B1.24), SVI parametrisation (B5.8), sticky strike (B5.7), OPRA (B1.24), market maker (B1.1), bid--ask spread (B1.1), adverse selection (B1.1), mid price (B1.1), inventory (B2.30).
- **Strategy files.** surface-fitted quoting across a listed chain; mass-quote making with quote protection; delta-hedged options book; event-aware options quoting; vega-limited skew quoting.
- **Tutorial.** Refit an SVI surface on every underlying move with firm.optmm, generate mass quotes, run a sweep across strikes against quote-protection settings, delta-hedge in the underlying, and enforce per-strike and per-expiry vega limits.
- **Build.** `firm.optquoter`: incremental surface refit, mass-quote generation with widths from the surface's uncertainty, quote-protection triggers (fill count, delta, vega per interval), delta hedger and bucketed limits; Python, on Book 5's firm.optmm and firm.svi.
- **Weekend problem.** Forty strikes in a millisecond — named result: the loss on a planted informed sweep as a function of the quote-protection threshold, and the fills given up by a tight threshold on normal days.
- **Facts to verify.** Cboe market-maker risk parameters (quote protection) rules (dated); OPRA message rates and capacity (dated); Muravyev 2016 Order flow and expected option returns (JF); Muravyev and Pearson 2020 Options trading costs are lower than you think (RFS); Public talks or papers by options market makers on automated quoting (dated; only with a citable source).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Cboe US options risk management tools: parameter types notional, volume (contracts traded), count (executions), percentage of quote (sum across series of an OSI root of % of quoted contracts executed); periods from 100 ms to a day; once reached, no new trades executed and trades in route rejected | Cboe web page | https://www.cboe.com/us/options/trading/risk_management/ | 2026-09-25 | "Count: number of executions"; "Percentage of Quote: sum across all series in an OSI Root of the percentage of contracts executed versus contracts quoted in each series during a specified time period"; "anywhere from a minimum of 100 milliseconds to a maximum of an entire day"; "no new trades will be executed and any trades in route will be rejected" | dat:hf:automated-options-market-making:cboe |
| F2 | Muravyev (2016): inventory risk of market makers has a first-order effect on option prices; price impact decomposed into inventory risk and asymmetric information, both large, inventory larger; imbalances due to inventory risk have five times larger impact than previously thought | Journal of Finance 71(2), 2016, 673-708 | https://api.crossref.org/works/10.1111/jofi.12380 | 2026-09-25 | Crossref abstract: "the inventory risk component is larger"; "five times larger impact on option prices than previously thought" | §3; strategy file |
| F3 | Muravyev and Pearson (2020): option price changes predictable at high frequency; traders time executions; effective spreads of timers under 40% of conventional measures; overall average effective spread one-quarter smaller | Review of Financial Studies 33(11), 2020, 4973-5014 | https://api.crossref.org/works/10.1093/rfs/hhaa010 | 2026-09-25 | Crossref abstract: "Effective spreads of traders who time executions are less than 40% of the size of conventional measures" | §1; strategy file |

## EXCLUDED

- OPRA message rates and capacity: not fetched; not stated.
- Public descriptions of named firms' automated quoting: none used (no citable primary source found in the time).
- Cboe US_Options_Risk_Management_Specification.pdf: served HTML to the fetcher; the web page is cited.
