# 26. Options Market Making in Practice — brief and source ledger

## Brief

- **Hook.** At 09:30:00 the opening auction prints; by 09:30:01 the market maker has refitted its surface for 3,000 series twice and re-sent every quote.
- **Sections.** Fitting a live surface; Theoretical value and quote widths; Delta-hedging policies; Pin risk, dividends and early exercise; Bucketed limits.
- **Defines.** theoretical value, hedging band, dividend play, vega bucket.
- **Uses (defined earlier).** options market maker, quoting obligation (Book 1 ch. 24), pin risk, assignment (Book 1 ch. 23), adverse selection, bid--ask spread (Book 1 ch. 1), mark-out (Book 2 ch. 15), edge (Book 2 ch. 29), width (Book 2 ch. 30), SVI parametrisation (ch. 8), sticky strike (ch. 7), early-exercise premium (ch. 6), gamma, vega.
- **Tutorial.** Run a toy options market maker on a simulated underlying and order flow: refit an SVI surface every second, quote widths set by vega and mark-outs, hedge inside a band, and report P&L by source and vega by bucket.
- **Build.** `firm.optmm`: options quoting engine (theoretical value from a live surface, width model, band delta hedger, bucketed vega and gamma limits).
- **Weekend problem.** The dividend-play morning — named result: the expected profit of a dividend play on one call series when a given share of holders fails to exercise, net of fees.
- **Facts to verify.** Pool, Stoll, Whaley 2008 dividend-play profits; exchange fee caps for dividend strategies (fee schedules, dated); Whalley-Wilmott 1997 hedging bands; OCC exercise statistics; market-maker obligations (reuse Book 1 ledger).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Pool, Stoll and Whaley, "Failure to exercise call options: an anomaly and a trading game", Journal of Financial Markets 11(1) (2008) 1-35; working-paper abstract: US exchange-traded options are unprotected from cash dividends, so exercising deep in-the-money calls the day before the ex-date can be optimal; in a sample of calls on stocks with quarterly dividends of at least a penny (January 1996 - April 2006) more than half of outstanding long positions went unexercised; holders lost over $491 million over ten years; market makers captured the lion's share with a dividend spread trading strategy | Crossref records 10.1016/j.finmar.2007.09.001 and (abstract) 10.2139/ssrn.972613 | https://api.crossref.org/works/10.2139/ssrn.972613 | 2026-09-24 | abstract in Crossref (SSRN version) | sec. dividends; def dividend play; omsources |
| F2 | Whalley and Wilmott, "An asymptotic analysis of an optimal hedging model for option pricing with transaction costs", Mathematical Finance 7(3) (1997) 307-324: small-cost asymptotics of the utility-based hedging problem; a simple analytical expression for the hedging strategy involving the option's gamma | Crossref record with abstract, 10.1111/1467-9965.00034 | https://api.crossref.org/works/10.1111/1467-9965.00034 | 2026-09-24 | abstract in Crossref | sec. delta-hedging policies; omsources |
| F3 | Cboe Exchange fees schedule of 15 September 2026, footnote 13: market-maker and other non-customer transaction fees are capped at $0.00 for merger, short stock interest, reversal, conversion and jelly roll strategies executed in open outcry on the same trading day in the same option class; dividend strategies are not among the listed strategies | Cboe Exchange, Inc., Fees Schedule (PDF) | https://cdn.cboe.com/resources/membership/Cboe_FeeSchedule.pdf | 2026-09-24 | footnote 13 (pdftotext) | dat:dv:options-market-making-in-practice:fees |

## EXCLUDED

- OCC exercise statistics: not fetched; not cited.
- Earlier exchange fee caps for dividend strategies: history not verified; the dated box states only the current schedule.
- Market-maker obligations: covered in Book 1 ch. 24 (its ledger); referred to in prose only.
- The hook's numbers are the chapter's model, not a real episode.
