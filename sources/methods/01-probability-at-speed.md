# 1. Probability at Speed — brief and source ledger

## Brief

- **Hook.** At 15:50 the exchange publishes the closing imbalance and the desk's running estimate of the closing price jumps by 14 cents; a researcher asks whether the estimate's revisions before 15:50 could have been predicted, because if they could, the estimate was leaving money on the table.
- **Sections.** Information: sigma-algebras, filtrations and conditional expectation; Martingales and the Doob martingale of a forecast; Stopping times and optional stopping; Changing the measure; The notation of the series.
- **Defines.** filtration, adapted process, conditional expectation, characteristic function, martingale, submartingale, supermartingale, Doob martingale, stopping time, uniform integrability, change of measure, equivalent measures, Radon--Nikodym derivative, density process.
- **Uses (defined earlier).** Bayesian update, fair value, call auction, order imbalance, variance.
- **Results (named theorems, not terms).** central limit theorem (recalled, with the Lindeberg condition); optional stopping theorem; Doob's maximal inequality; abstract Bayes formula for conditional expectations under a change of measure; orthogonality of martingale increments (variance decomposition).
- **Tutorial.** Build the Doob martingale of the five-card game of One Quant Book 2, chapter 30 (the expected sum as cards are revealed), check that its revisions have mean zero and are uncorrelated with the past, then break the property with a forecaster that under-reacts and measure the predictability it leaves.
- **Build.** `firm.mgtest`: martingale diagnostics for a forecast series (revision-on-past regressions, variance-ratio and runs statistics, variance decomposition of revisions by time bucket); Python.
- **Weekend problem.** The fair value of the close — a closing price built from intraday increments plus an imbalance jump at 15:50; named result: the share of the day's closing-price variance resolved after the 15:50 imbalance publication, from the orthogonal-increments decomposition of the Doob martingale.
- **Facts to verify.** NYSE and Nasdaq closing-imbalance publication from 15:50 (reuse Book 1 ch. 13 ledger rows F1-F2); Kolmogorov 1933, Grundbegriffe der Wahrscheinlichkeitsrechnung (axioms); Ville 1939 introduces the word martingale; Doob 1953, Stochastic Processes; Radon-Nikodym theorem (Nikodym 1930).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Kolmogorov's Grundbegriffe der Wahrscheinlichkeitsrechnung (Springer, Berlin, 1933) set out the measure-theoretic axioms of probability | Springer Nature Link, book record 10.1007/978-3-642-49888-6; Shafer and Vovk, "The origins and legacy of Kolmogorov's Grundbegriffe" | https://link.springer.com/book/10.1007/978-3-642-49888-6 | 2026-09-24 | "Grundbegriffe der Wahrscheinlichkeitsrechnung", Springer 1933 | §1 intro; omsources |
| F2 | The word martingale entered probability in Jean Ville's thesis "Étude critique de la notion de collectif" (Gauthier-Villars, Paris, 1939, Borel's monograph series) | Bienvenu, Shafer and Shen, "On the history of martingales in the study of randomness", JEHPS 2009 | https://www.jehps.net/juin2009/BienvenuShaferShen.pdf | 2026-09-24 | Ville "exposed in his thesis Étude critique de la notion de collectif (Paris, 1939)" the notion of martingale; also EUDML record https://eudml.org/doc/192893 | omsources |
| F3 | J. L. Doob, Stochastic Processes, John Wiley and Sons, New York, 1953 (reviewed in Bull. AMS 1954) | AMS Bulletin review, vol. 60 no. 2 (1954) | https://www.ams.org/journals/bull/1954-60-02/S0002-9904-1954-09801-4/S0002-9904-1954-09801-4.pdf | 2026-09-24 | "Stochastic processes. By J. L. Doob. New York, Wiley, 1953" | omsources |
| F4 | O. Nikodym, "Sur une généralisation des intégrales de M. J. Radon", Fundamenta Mathematicae 15 (1930), 131-179 | IMPAN journal page (DOI 10.4064/fm-15-1-131-179) | https://www.impan.pl/pl/wydawnictwa/czasopisma-i-serie-wydawnicze/fundamenta-mathematicae/all/15/0/92816/sur-une-generalisation-des-integrales-de-m-j-radon | 2026-09-24 | Fundamenta Mathematicae 15 (1930), 131-179 | omsources |
| F5 | D. Williams, Probability with Martingales, Cambridge University Press, 1991 (Cambridge Mathematical Textbooks) | Cambridge University Press book page | https://www.cambridge.org/highereducation/books/probability-with-martingales/B4CFCE0D08930FB46C6E93E775503926 | 2026-09-24 | publisher record, 1991 | §1 (CLT, admitted proofs); omsources |
| F6 | The closing-auction imbalance is published ten minutes before the close on the US primary exchanges (NYSE regulatory imbalance at 15:50; Nasdaq dissemination from 15:50) | One Quant Book 1, chapter 13 ledger rows F1-F2 (NYSE Closing Process fact sheet; Nasdaq Closing Cross FAQ) | https://www.nyse.com/publicdocs/nyse/NYSE_Auctions_Closing_Process_Fact_Sheet.pdf | 2026-09-18 | Book 1 ledger: "imbalance of at least 500 round lots" published at 15:50; the chapter states the scene only and points to Book 1 for the venue rules | hook; problem |

## EXCLUDED

- Lévy 1934 as the first to study martingale-like processes (named in the history paper): not needed in the text; not stated.
- Mathematics (conditional expectation, optional stopping, the closing-price model, the card game) is derived in the chapter and checked by `test_solutions.py`; no source needed.

