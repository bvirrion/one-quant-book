# 12. Testing and Multiple Testing — brief and source ledger

## Brief

- **Hook.** A research team tries 200 variants of a momentum signal and the best has a backtest t-statistic of 3.1. If none of them works, the largest of 200 independent t-statistics exceeds 3.1 about one time in six.
- **Sections.** Tests, size and power; The garden of forking paths; Family-wise error and false discoveries; Reality-check tests for strategy search.
- **Defines.** hypothesis test, null hypothesis, p-value, size of a test, power of a test, likelihood-ratio test, Kolmogorov--Smirnov test, multiple testing, data snooping, garden of forking paths, family-wise error rate, Bonferroni correction, Holm procedure, false discovery rate, Benjamini--Hochberg procedure, Reality Check, superior predictive ability test, deflated Sharpe ratio.
- **Uses (defined earlier).** estimator, standard error, Sharpe ratio, likelihood function, maximum likelihood estimator, HAC estimator.
- **Results (named theorems, not terms).** Neyman-Pearson lemma; Wilks' theorem (stated); Bonferroni and Holm control the family-wise error rate; Benjamini-Hochberg controls the false discovery rate under independence (and positive dependence); sample size needed to detect a Sharpe ratio at given size and power; the maximum of correlated test statistics: the max-t null by simulation.
- **Tutorial.** Generate 200 correlated noise strategies, pick the best, and compare its naive p-value with Bonferroni, Holm, Benjamini-Hochberg and a max-statistic p-value simulated from the estimated correlation matrix; show how correlation among variants makes Bonferroni conservative.
- **Build.** `firm.multitest`: multiple-testing module (Bonferroni, Holm, Benjamini-Hochberg, Benjamini-Yekutieli, max-statistic p-values by Gaussian simulation with a hook for the bootstrap of chapter 13, deflated Sharpe ratio); Python.
- **Weekend problem.** Two hundred momentum variants — named result: the adjusted p-value of the best of 200 correlated variants and the effective number of independent trials the search amounts to.
- **Facts to verify.** Neyman and Pearson 1933 (Phil. Trans. Royal Society A); Holm 1979 (Scandinavian J. Statistics); Benjamini and Hochberg 1995 (JRSS B); Benjamini and Yekutieli 2001 (Annals of Statistics); White 2000 (Econometrica) reality check; Hansen 2005 (J. Business and Economic Statistics) SPA test; Romano and Wolf 2005 (Econometrica) stepwise multiple testing; Harvey, Liu and Zhu 2016 (Review of Financial Studies) t > 3 hurdle; Bailey and López de Prado 2014 (J. Portfolio Management) deflated Sharpe ratio; Gelman and Loken 2013/2014 garden of forking paths; Kolmogorov 1933 / Smirnov 1948.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | J. Neyman and E. S. Pearson, "On the problem of the most efficient tests of statistical hypotheses", Phil. Trans. Royal Society A 231 (1933), 289-337 | Crossref record, doi 10.1098/rsta.1933.0009 | https://doi.org/10.1098/rsta.1933.0009 | 2026-09-24 | vol 231, pp 289-337, 1933 | thm Neyman-Pearson; omsources |
| F2 | S. Holm, "A simple sequentially rejective multiple test procedure", Scandinavian Journal of Statistics 6(2) (1979), 65-70 | Wikipedia citation (JSTOR 4615733, MR 538597) | https://www.jstor.org/stable/4615733 | 2026-09-24 | vol 6, issue 2, pp 65-70 | def Holm; omsources |
| F3 | Y. Benjamini and Y. Hochberg, "Controlling the false discovery rate: a practical and powerful approach to multiple testing", JRSS B 57(1) (1995), 289-300 | Crossref record | https://doi.org/10.1111/j.2517-6161.1995.tb02031.x | 2026-09-24 | vol 57(1), pp 289-300 | thm BH; omsources |
| F4 | Y. Benjamini and D. Yekutieli, "The control of the false discovery rate in multiple testing under dependency", Annals of Statistics 29(4) (2001): FDR control under positive dependence and the harmonic correction | Crossref record | https://doi.org/10.1214/aos/1013699998 | 2026-09-24 | vol 29(4), 2001 | thm BH (dependence); omsources |
| F5 | H. White, "A reality check for data snooping", Econometrica 68(5) (2000), 1097-1126 | Crossref record | https://doi.org/10.1111/1468-0262.00152 | 2026-09-24 | vol 68(5), pp 1097-1126 | def Reality Check; omsources |
| F6 | P. R. Hansen, "A test for superior predictive ability", Journal of Business and Economic Statistics 23(4) (2005), 365-380 | Crossref record | https://doi.org/10.1198/073500105000000063 | 2026-09-24 | vol 23(4), pp 365-380 | def SPA; omsources |
| F7 | J. P. Romano and M. Wolf, "Stepwise multiple testing as formalized data snooping", Econometrica 73(4) (2005), 1237-1282 | Crossref record | https://doi.org/10.1111/j.1468-0262.2005.00615.x | 2026-09-24 | vol 73(4), pp 1237-1282 | method max-t step-down; omsources |
| F8 | C. R. Harvey, Y. Liu and H. Zhu, "... and the cross-section of expected returns", Review of Financial Studies 29(1) (2016), 5-68: a newly discovered factor needs a t-ratio above 3 | Crossref record; NBER w20592 abstract | https://www.nber.org/papers/w20592 | 2026-09-24 | "a newly discovered factor needs to clear a much higher hurdle, with a t-ratio greater than 3" | section 4; omsources |
| F9 | D. H. Bailey and M. Lopez de Prado, "The deflated Sharpe ratio: correcting for selection bias, backtest overfitting, and non-normality", Journal of Portfolio Management 40(5) (2014), 94-107 | Crossref record | https://doi.org/10.3905/jpm.2014.40.5.094 | 2026-09-24 | vol 40(5), pp 94-107 | def deflated Sharpe ratio; omsources |
| F10 | A. Gelman and E. Loken, "The garden of forking paths: why multiple comparisons can be a problem, even when there is no fishing expedition or p-hacking and the research hypothesis was posited ahead of time", working paper, 14 Nov 2013 | author's PDF (Columbia) | https://sites.stat.columbia.edu/gelman/research/unpublished/p_hacking.pdf | 2026-09-24 | title page dated 14 Nov 2013; "Researcher degrees of freedom can lead to a multiple comparisons problem, even in settings where researchers perform only a single analysis" | def garden of forking paths; omsources |
| F11 | H. W. Lilliefors, "On the Kolmogorov-Smirnov test for normality with mean and variance unknown", JASA 62(318) (1967), 399-402 | Crossref record | https://doi.org/10.1080/01621459.1967.10482916 | 2026-09-24 | vol 62(318), pp 399-402 | section 1 (KS with fitted parameters); iq 7 solution |

## EXCLUDED

- Kolmogorov 1933 and Smirnov 1948 (planned): the text names the test only, no bibliographic claim.
- The Kolmogorov limit law and its 5% point 1.358 are derived and computed in `qm_testing.kolmogorov_sf`, not sourced.
- The momentum family, the random walk and the thousand-signal screen are simulations, not market facts.

