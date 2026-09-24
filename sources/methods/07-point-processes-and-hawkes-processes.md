# 7. Point Processes and Hawkes Processes — brief and source ledger

## Brief

- **Hook.** Count the trades in a liquid future in one-second bins over a busy morning: the variance of the counts is many times their mean, and bursts follow bursts within milliseconds. A Poisson clock cannot do that; a process whose events raise the rate of further events can.
- **Sections.** Intensities and compensators; Self- and mutual excitation; Likelihood estimation; Simulation by thinning and by branching; Diagnostics by time change.
- **Defines.** point process, counting process, conditional intensity, compensator, inhomogeneous Poisson process, Cox process, Hawkes process, excitation kernel, branching ratio, multivariate Hawkes process, thinning.
- **Uses (defined earlier).** Poisson process, compensated Poisson process, hazard rate, martingale, filtration, stopping time.
- **Results (named theorems, not terms).** Doob-Meyer compensator of a counting process (stated); time-rescaling theorem; cluster (branching) representation of a Hawkes process; stationarity condition and mean intensity mu / (1 - ||g||_1); log-likelihood of a point process and its O(n) recursion for exponential kernels.
- **Tutorial.** Simulate an exponential-kernel Hawkes process by Ogata's thinning, fit it by maximum likelihood with the O(n) recursion, and check that the time-rescaled residuals are unit exponential.
- **Build.** `firm.hawkes`: univariate and multivariate exponential-kernel Hawkes processes: thinning and branching simulators, O(n) log-likelihood and gradient, maximum-likelihood fit, residual diagnostics; Python, C++20 and Rust.
- **Weekend problem.** The self-exciting tape — named result: the branching ratio recovered from a simulated trading day, and the spurious branching ratio obtained when an intraday seasonal baseline is ignored.
- **Facts to verify.** Hawkes 1971 (Biometrika) spectra of self-exciting point processes; Hawkes and Oakes 1974 cluster representation; Ogata 1981 (IEEE Trans. Information Theory) thinning; Filimonov and Sornette 2012 (Physical Review E) reflexivity index; Hardiman, Bercot and Bouchaud 2013 (EPJ B) branching ratio near one for E-mini; Bacry, Mastromatteo and Muzy 2015 (Market Microstructure and Liquidity) review; Brown, Barbieri et al. 2002 time-rescaling theorem (Neural Computation).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | A. G. Hawkes, "Spectra of some self-exciting and mutually exciting point processes", Biometrika 58(1) (1971), 83-90 | Oxford Academic record | https://academic.oup.com/biomet/article-abstract/58/1/83/224809 | 2026-09-24 | Biometrika 58(1), 83-90 | def Hawkes; omsources |
| F2 | A. G. Hawkes and D. Oakes, "A cluster process representation of a self-exciting process", Journal of Applied Probability 11(3) (1974), 493-503: every stationary self-exciting process with finite intensity is a Poisson cluster (immigration-birth) process | Semantic Scholar record and search summary | https://www.semanticscholar.org/paper/A-cluster-process-representation-of-a-self-exciting-Hawkes-Oakes/0aa934cc6b5ec9fcc1d7cc3da01741be9242513b | 2026-09-24 | "may be represented as Poisson cluster processes which are age-dependent immigration-birth processes" | thm cluster representation; omsources |
| F3 | Y. Ogata, "On Lewis' simulation method for point processes", IEEE Transactions on Information Theory 27(1) (1981), 23-31: thinning for conditional intensities | ACM DL record, doi 10.1109/TIT.1981.1056305 | https://dl.acm.org/doi/10.1109/TIT.1981.1056305 | 2026-09-24 | "based on the thinning algorithm which was introduced by Lewis and Shedler" | method Ogata; omsources |
| F4 | Brown, Barbieri, Ventura, Kass and Frank, "The time-rescaling theorem and its application to neural spike train data analysis", Neural Computation 14(2) (2002), 325-346 | PubMed 11802915 | https://pubmed.ncbi.nlm.nih.gov/11802915/ | 2026-09-24 | "any point process with an integrable conditional intensity function may be transformed into a Poisson process with unit rate" | thm time-rescaling; omsources |
| F5 | Hardiman, Bercot and Bouchaud, "Critical reflexivity in financial markets: a Hawkes process analysis", European Physical Journal B 86 (2013), 442: mid-price changes of the E-mini S&P futures; the Hawkes kernel "integrates to unity independently of the analysed period, from 1998 to 2011" | arXiv 1302.1405 abstract | https://arxiv.org/abs/1302.1405 | 2026-09-24 | "the Hawkes kernel integrates to unity independently of the analysed period, from 1998 to 2011" | hook; omsources |
| F6 | Filimonov and Sornette, "Quantifying reflexivity in financial markets: toward a prediction of flash crashes", Physical Review E 85, 056108 (2012): E-mini S&P futures 1998-2010, share of price changes due to exogenous information fell from 70% in 1998 to less than 30% since 2007 (branching ratio from about 0.3 to above 0.7) | arXiv 1201.3572 / Phys. Rev. E record | https://link.aps.org/doi/10.1103/PhysRevE.85.056108 | 2026-09-24 | "only 70% in 1998 to less than 30% since 2007 of the price changes resulting from some revealed exogenous information" | hook; omsources |
| F7 | Filimonov and Sornette, "Apparent criticality and calibration issues in the Hawkes self-excited point process model: application to high-frequency financial data", Quantitative Finance 15(8) (2015), 1293-1314: calibrating on mixtures of Poisson processes with regime changes gives spurious near-critical branching ratios | arXiv 1308.6756 / Taylor & Francis record | https://arxiv.org/abs/1308.6756 | 2026-09-24 | "calibrating the Hawkes process on mixtures of pure Poisson processes with regime changes leads to spurious apparent critical values for the branching ratio while the true value is actually zero" | hook; problem part III; omsources |

## EXCLUDED

- Bacry, Mastromatteo and Muzy 2015 review (planned): not cited in the text.
- The hook's 'variance several times the mean in one-minute bins' is illustrated by the chapter's simulation (ratio 10.5 at n = 0.7), not stated as a measured fact about a named contract.

