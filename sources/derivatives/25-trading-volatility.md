# 25. Trading Volatility — brief and source ledger

## Brief

- **Hook.** A trader buys one-month straddles at 18 volatility because the share has realised 25 for two months; four weeks later it has realised 24 and the position has lost money: the big moves came on days when the gamma was small.
- **Sections.** Gamma scalping; Volatility carry and the roll-down; Skew and term trades; Attributing a volatility book's P&L; The variance risk premium in practice.
- **Defines.** gamma scalping, implied--realised spread, volatility roll-down.
- **Uses (defined earlier).** P\&L attribution, carry (Book 1 ch. 7), risk reversal (Book 2 ch. 19), straddle, hedging P\&L, vega, theta, vanna, volga (ch. 4), sticky strike, sticky delta (ch. 7), variance risk premium (ch. 14), stochastic volatility model (ch. 10), delta--gamma approximation (Book 6 ch. 21).
- **Tutorial.** Run a gamma-scalping book on simulated paths with stochastic volatility and attribute its daily P&L into delta, gamma, theta, vega, vanna, volga and unexplained; show how the attribution changes between sticky-strike and sticky-delta marking.
- **Build.** `firm.volpnl`: volatility-book P&L attribution (Greek-based explain against full revaluation, sticky-strike and sticky-delta marking, unexplained P&L).
- **Weekend problem.** The wrong days — named result: the gamma P&L of a long straddle when the same realised volatility comes in moves concentrated on low-gamma days, against uniformly spread moves.
- **Facts to verify.** Bakshi-Kapadia 2003 RFS delta-hedged gains; Carr-Wu 2009 variance risk premium size; Cboe PUT and BXM index methodology; 5 February 2018 (reuse Book 1 ledger); Israelov-Nielsen 2015 on covered calls.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Bakshi and Kapadia, "Delta-hedged gains and the negative market volatility risk premium", Review of Financial Studies 16(2) (2003) 527-566; working-paper abstract: on S&P 500 index options the delta-hedged strategy underperforms zero, less so away from the money and more at times of higher volatility; evidence of a negative market volatility risk premium | Crossref records 10.1093/rfs/hhg002 and (abstract) 10.2139/ssrn.267106 | https://api.crossref.org/works/10.2139/ssrn.267106 | 2026-09-24 | abstract in Crossref (SSRN version) | sec. variance risk premium, omsources |
| F2 | Israelov and Nielsen, "Covered calls uncovered", Financial Analysts Journal 71(6) (2015) 44-57; working-paper abstract: a covered call's short-volatility exposure has had a realised Sharpe ratio close to 1.0 but contributes less than 10 percent of its risk; the embedded equity-reversal exposure is about a quarter of the risk with little reward | Crossref records 10.2469/faj.v71.n6.1 and (abstract) 10.2139/ssrn.2444999 | https://api.crossref.org/works/10.2139/ssrn.2444999 | 2026-09-24 | abstract in Crossref (SSRN version) | sec. variance risk premium, omsources |
| F3 | Cboe S&P 500 PutWrite Index (PUT): short at-the-money SPX puts over a Treasury-bill account (one- and three-month bills); puts sold monthly, usually on the third Friday; strike = listed SPX strike closest to but not greater than the last S&P 500 value reported before 11:00 a.m. ET | Cboe, "Cboe S&P 500 PutWrite Indices Methodology" (PDF) | https://cdn.cboe.com/api/global/us_indices/governance/Cboe_SP_500_PutWrite_Indices_Methodology.pdf | 2026-09-24 | sections 1.1 and 2.2 of the PDF | dat:dv:trading-volatility:put |
| F4 | 5 February 2018: the S&P 500 fell 4% while the VIX jumped 20 points | BIS Quarterly Review, March 2018, box "The equity market turbulence of 5 February" (also Book 1 ch. 25 ledger F3) | https://www.bis.org/publ/qtrpdf/r_qt1803t.htm | 2026-09-24 | "the S&P 500 index fell 4% while the VIX ... jumped 20 points" | sec. variance risk premium |
| F5 | Carr and Wu, "Variance risk premiums", Review of Financial Studies 22(3) (2009) 1311-1341 (concept only; see chapter 14 ledger F4) | Crossref record 10.1093/rfs/hhn038 | https://api.crossref.org/works/10.1093/rfs/hhn038 | 2026-09-24 | Crossref metadata | omsources |

## EXCLUDED

- Cboe BXM (buy-write) methodology: not fetched; not cited.
- Measured sizes of the variance risk premium (Carr-Wu 2009): abstract not available; the chapter's premium of two points is an assumption of its simulation, labelled as such.
- The hook is the chapter's constructed path, not a real trade.
