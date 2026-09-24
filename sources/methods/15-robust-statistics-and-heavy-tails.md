# 15. Robust Statistics and Heavy Tails — brief and source ledger

## Brief

- **Hook.** One bad print in the feed, a trade at 10.00 instead of 100.00, multiplies the 250-day standard deviation of a stock's returns by four, and moves its median absolute deviation not at all.
- **Sections.** Robust losses and the influence function; Winsorising, trimming and rank methods; Heavy tails; Extreme-value theory; Estimating the tail index.
- **Defines.** influence function, breakdown point, Huber loss, median absolute deviation, winsorisation, trimmed mean, rank correlation, Spearman's rank correlation, Kendall's tau, copula, tail dependence coefficient, heavy-tailed distribution, tail index, extreme-value theory, generalised extreme value distribution, generalised Pareto distribution, peaks over threshold, Hill estimator.
- **Uses (defined earlier).** clearly erroneous trade, M-estimator, estimator, maximum likelihood estimator, bootstrap, variance, realised volatility, quasi-maximum likelihood.
- **Results (named theorems, not terms).** breakdown points of the mean (0) and the median (1/2); Sklar's theorem; Fisher-Tippett-Gnedenko theorem; Pickands-Balkema-de Haan theorem; moments of order at least the tail index do not exist; asymptotic normality of the Hill estimator (stated).
- **Tutorial.** Estimate the tail index of daily EUR/USD returns (ECB reference rates) with the Hill estimator and a peaks-over-threshold fit; read a Hill plot; compare the one-in-a-thousand-days loss from the normal, the Student t and the generalised Pareto fits.
- **Build.** `firm.robust`: robust location and scale (Huber, MAD, Qn), winsorisers, rank correlations, Hill estimator with threshold diagnostics, generalised Pareto fit by maximum likelihood, tail quantiles; Python.
- **Weekend problem.** The bad tick — named result: the 99.9% daily loss quantile of EUR/USD under the normal, Student t and generalised Pareto fits, and the error one erroneous print introduces into each.
- **Facts to verify.** ECB euro reference rate USD per EUR daily since 1999 (dataset, licence); Huber 1964 (Annals of Mathematical Statistics); Hampel 1974 (JASA) influence curve; Fisher and Tippett 1928; Gnedenko 1943; Balkema and de Haan 1974; Pickands 1975; Hill 1975 (Annals of Statistics); Sklar 1959; Mandelbrot 1963 (Journal of Business) cotton prices; Rousseeuw and Croux 1993 (JASA) Qn estimator.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | ECB euro foreign exchange reference rates, USD, JPY and GBP per euro, daily 4 Jan 1999 to 23 Sep 2026 (series EXR.D.USD.EUR.SP00.A etc.); 1.1572 USD per EUR on 24 Mar 2026 | ECB Data Portal API (csvdata) | https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?format=csvdata | 2026-09-24 | 7,099 common days; TITLE 'US dollar/Euro ECB reference exchange rate' | tutorial, all figures, problem; data/methods/eur_fx_ecb_1999_2026.csv |
| F2 | ESCB statistics may be reused free of charge provided the source is quoted | ECB, Policy regarding the reuse of ESCB statistics | https://www.ecb.europa.eu/stats/ecb_statistics/governance_and_quality_framework/html/usage_policy.en.html | 2026-09-24 | "may be reused free of charge on the condition that the source is quoted" | data/methods/LICENSES.md; figure captions |
| F3 | P. J. Huber, "Robust estimation of a location parameter", Annals of Mathematical Statistics 35(1) (1964), 73-101 | Crossref record | https://doi.org/10.1214/aoms/1177703732 | 2026-09-24 | vol 35(1), pp 73-101 | def Huber loss; omsources |
| F4 | F. R. Hampel, "The influence curve and its role in robust estimation", JASA 69(346) (1974), 383-393 | Crossref record | https://doi.org/10.1080/01621459.1974.10482962 | 2026-09-24 | vol 69(346), pp 383-393 | def influence function; omsources |
| F5 | P. J. Rousseeuw and C. Croux, "Alternatives to the median absolute deviation", JASA 88(424) (1993), 1273-1283 (the Qn estimator) | Crossref record | https://doi.org/10.1080/01621459.1993.10476408 | 2026-09-24 | vol 88(424), pp 1273-1283 | section 1; firm.robust; omsources |
| F6 | A. Sklar, "Fonctions de repartition a n dimensions et leurs marges", Publ. Inst. Statist. Univ. Paris 8 (1959), 229-231 | Wikipedia citation (Copula (statistics)) | https://en.wikipedia.org/wiki/Copula_(statistics) | 2026-09-24 | vol 8, pp 229-231, 1959 | thm Sklar; omsources |
| F7 | R. A. Fisher and L. H. C. Tippett, "Limiting forms of the frequency distribution of the largest or smallest member of a sample", Proc. Cambridge Phil. Soc. 24(2) (1928), 180-190 | Crossref record | https://doi.org/10.1017/S0305004100015681 | 2026-09-24 | vol 24(2), pp 180-190 | thm FTG; omsources |
| F8 | B. Gnedenko, "Sur la distribution limite du terme maximum d'une serie aleatoire", Annals of Mathematics 44(3) (1943), 423-453 | Crossref record | https://doi.org/10.2307/1968974 | 2026-09-24 | vol 44(3), from p. 423 | thm FTG; omsources |
| F9 | A. A. Balkema and L. de Haan, "Residual life time at great age", Annals of Probability 2(5) (1974) | Crossref record | https://doi.org/10.1214/aop/1176996548 | 2026-09-24 | vol 2(5), 1974 | thm PBdH; omsources |
| F10 | J. Pickands III, "Statistical inference using extreme order statistics", Annals of Statistics 3(1) (1975) | Crossref record | https://doi.org/10.1214/aos/1176343003 | 2026-09-24 | vol 3(1), 1975 | thm PBdH; omsources |
| F11 | B. M. Hill, "A simple general approach to inference about the tail of a distribution", Annals of Statistics 3(5) (1975) | Crossref record | https://doi.org/10.1214/aos/1176343247 | 2026-09-24 | vol 3(5), 1975 | def Hill estimator; omsources |
| F12 | B. Mandelbrot, "The variation of certain speculative prices", Journal of Business 36(4) (1963), from p. 394 (cotton prices; stable laws) | Crossref record | https://doi.org/10.1086/294632 | 2026-09-24 | vol 36(4), p 394 | section 3; omsources |
| F13 | R. Cont, "Empirical properties of asset returns: stylized facts and statistical issues", Quantitative Finance 1(2) (2001), 223-236: tail index of returns finite, higher than two and less than five for most data sets studied | Crossref record; the article (Wharton course mirror PDF) | https://doi.org/10.1080/713665670 | 2026-09-24 | stylised fact 2: "a tail index which is finite, higher than two and less than five for most data sets studied" (http://www-stat.wharton.upenn.edu/~steele/Resources/FTSResources/StylizedFacts/Cont2001.pdf) | section 2; omsources |

## EXCLUDED

- "Daily returns of liquid assets typically have tail indices between 3 and 5": replaced in Phase C by Cont (2001)'s sourced statement (between two and five for most data sets), new last F row.
- Qn and MAD Gaussian efficiencies (82%, 37%): not stated; only Huber's 95% at c = 1.345, which the numbers test computes.
- The bad print (1.5172 for 1.1572 on 24 Mar 2026) is a constructed corruption, not an event in the ECB series. Brief deviation: the hook uses a transposed-digit EUR/USD print (x7 on the 250-day sd) instead of a stock trading at 10.00 for 100.00, to keep one data set through the chapter.

