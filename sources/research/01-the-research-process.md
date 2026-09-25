# 1. The Research Process — brief and source ledger

## Brief

- **Hook.** A researcher shows a backtest with a Sharpe ratio of 2.4 on Friday; on Monday the head of research asks how many variants were tried, and which came first, the hypothesis or the chart. Nobody wrote it down.
- **Sections.** Hypothesis first; The research log and the trial count; What counts as evidence; From idea to production; Research as a portfolio of bets.
- **Defines.** research hypothesis, economic rationale, research log, trial count, pre-registration, holdout set, stage gate, kill criterion, research review.
- **Uses (defined earlier).** alpha (B1.1), Sharpe ratio (B4.11), multiple testing (B4.12), data snooping (B4.12), garden of forking paths (B4.12), deflated Sharpe ratio (B4.12), p-value (B4.12), power of a test (B4.12).
- **Tutorial.** Create a research log with firm.researchlog, log a 50-variant search of a planted-noise signal, and watch the logged trial count move the deflated Sharpe ratio of the winner; then replay the same search unlogged.
- **Build.** `firm.researchlog`: append-only, hash-chained experiment registry (hypothesis, family, code hash, data snapshot id, parameters, metrics, timestamps) with trial counting per hypothesis family; Python.
- **Weekend problem.** The Friday backtest — named result: the probability that a researcher with no edge who tries twenty variants a week shows a Sharpe ratio of at least 2 within a year, and the deflated Sharpe ratio of that backtest once the log's trial count is used.
- **Facts to verify.** Bailey, Borwein, Lopez de Prado, Zhu 2014, Pseudo-mathematics and financial charlatanism (Notices AMS); Nosek et al. 2018, The preregistration revolution (PNAS); Harvey, Liu, Zhu 2016 (RFS) t > 3 hurdle; Arnott, Harvey, Markowitz 2019, A backtesting protocol in the era of machine learning (JFDS); Lopez de Prado 2018, The 10 reasons most machine learning funds fail (JPM).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | J. P. A. Ioannidis, "Why most published research findings are false", PLoS Medicine 2(8) e124 (2005): PPV = (1 - beta) R / (R - beta R + alpha), R the pre-study odds | Crossref record; article PDF (open access) | https://doi.org/10.1371/journal.pmed.0020124 | 2026-09-24 | "one gets PPV = (1 - beta)R/(R - betaR + alpha)" (section "Modeling the framework for false positive findings") | prop. PPV; omsources |
| F2 | R. D. Arnott, C. R. Harvey, H. Markowitz, "A backtesting protocol in the era of machine learning", J. Financial Data Science 1(1) (2019) 64-74: Exhibit 1 is a long-short NYSE strategy developed on 1963-1988, "validated out of sample with even stronger results over the years 1989 through 2015", "nearly 6% alpha a year", no significant correlation with the market or value, size and momentum, turnover "less than 10% a year", built from the letters of ticker symbols (all combinations of the first three letters) | author's copy (Duke) of the published article; Crossref record | https://people.duke.edu/~charvey/Research/Published_Papers/P138_A_backtesting_protocol.pdf | 2026-09-24 | quotes as given, p. 65-66; "This data-mined strategy forms portfolios based on letters in a company's ticker symbol" | section 1 (the ticker-letter strategy); omsources |
| F3 | Same article: "Keep track of what is tried"; twenty variables with interactions give 20 choose 2 = 190 possible interactions (footnote 7); seven categories (research motivation, multiple testing and statistical methods, sample choice and data, cross-validation, model dynamics, model complexity, research culture) | as F2 | https://doi.org/10.3905/jfds.2019.1.064 | 2026-09-24 | "This single interaction does not translate into only 22 tests ... but into 190 possible interactions" | rem. combinations count |
| F4 | B. A. Nosek, C. R. Ebersole, A. C. DeHaven, D. T. Mellor, "The preregistration revolution", PNAS 115(11) (2018) 2600-2606: preregistration defines the research questions and analysis plan before observing outcomes and distinguishes prediction from postdiction | Crossref record with abstract | https://doi.org/10.1073/pnas.1708274114 | 2026-09-24 | "Preregistration distinguishes analyses and outcomes that result from predictions from those that result from postdictions" | section 3; omsources |
| F5 | D. H. Bailey, J. M. Borwein, M. Lopez de Prado, Q. J. Zhu, "Pseudo-mathematics and financial charlatanism: the effects of backtest overfitting on out-of-sample performance", Notices of the AMS 61(5) (2014), from p. 458 | Crossref record (article PDF refused scripted and WebFetch access, 403) | https://doi.org/10.1090/noti1105 | 2026-09-24 | bibliographic record only; no claim of the paper is quoted in the chapter | omsources |
| F6 | M. Lopez de Prado, "The 10 reasons most machine learning funds fail", J. Portfolio Management 44(6) (2018) 120-133 | Crossref record | https://doi.org/10.3905/jpm.2018.44.6.120 | 2026-09-24 | bibliographic record only | omsources |
| F7 | C. R. Harvey, Y. Liu, H. Zhu, "... and the cross-section of expected returns", Review of Financial Studies 29(1) (2016) 5-68 | Crossref record | https://doi.org/10.1093/rfs/hhv059 | 2026-09-24 | vol 29(1), pp 5-68 | omsources |

## EXCLUDED

- The Friday researcher, the reversal hypothesis of the example and the two hundred-idea research group are illustrations, not facts.
- All probabilities, PPVs, deflated ratios and the tutorial's search are computed in `code/research/01-the-research-process/` (tested), not sourced.
- Bailey et al. 2014's minimum-backtest-length example (planned as a quote) was not stated: the article could not be fetched; chapter 20 derives the bound itself.
