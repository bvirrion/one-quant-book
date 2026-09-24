# 14. Bayesian Methods — brief and source ledger

## Brief

- **Hook.** A multi-manager platform reviews fifty portfolio managers; the best three-year Sharpe ratio is 2.4 and the allocation committee wants to double that manager's capital. Shrunk toward what fifty managers usually achieve, the same record is worth about half as much.
- **Sections.** Priors, posteriors and conjugacy; Shrinkage; Hierarchical models and empirical Bayes; Markov-chain Monte Carlo.
- **Defines.** prior distribution, posterior distribution, conjugate prior, posterior predictive distribution, credible interval, shrinkage estimator, James--Stein estimator, hierarchical model, empirical Bayes, Markov chain Monte Carlo, Metropolis--Hastings algorithm, Gibbs sampler, effective sample size, burn-in.
- **Uses (defined earlier).** Bayesian update, multi-manager platform, Sharpe ratio, likelihood function, maximum likelihood estimator, Markov chain, stationary distribution, detailed balance, standard error.
- **Results (named theorems, not terms).** James-Stein dominates the MLE in dimension three or more; posterior mean of the normal-normal model as a precision-weighted average; detailed balance of the Metropolis-Hastings kernel; Gibbs sampling as a special case of Metropolis-Hastings.
- **Tutorial.** Fit a hierarchical normal model to fifty managers' Sharpe ratios by empirical Bayes in closed form and by a Gibbs sampler; compare the shrinkage and check it on a second, out-of-sample period.
- **Build.** `firm.bayes`: conjugate updaters (beta-binomial, normal-normal, normal-inverse-gamma), empirical-Bayes shrinkage of normal means, random-walk Metropolis and a Gibbs sampler for the hierarchical normal model, with effective-sample-size and R-hat diagnostics; Python.
- **Weekend problem.** The allocator's shortlist — named result: the posterior mean Sharpe ratio of the best of fifty managers after empirical-Bayes shrinkage, and the out-of-sample reduction in mean squared error against the raw estimates.
- **Facts to verify.** Bayes 1763 (Phil. Trans.); James and Stein 1961 (Berkeley Symposium); Efron and Morris 1975 (JASA) baseball example; Robbins 1956 empirical Bayes; Metropolis et al. 1953 (J. Chemical Physics); Hastings 1970 (Biometrika); Geman and Geman 1984 (IEEE PAMI) Gibbs sampler; Gelman and Rubin 1992 (Statistical Science) R-hat.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | T. Bayes, "An essay towards solving a problem in the doctrine of chances", Phil. Trans. Royal Society 53 (1763), 370-418 (communicated by R. Price) | Crossref record | https://doi.org/10.1098/rstl.1763.0053 | 2026-09-24 | issue 53, pp 370-418, 1763 | def prior/posterior; omsources |
| F2 | W. James and C. Stein, "Estimation with quadratic loss", Proc. Fourth Berkeley Symposium on Mathematical Statistics and Probability, vol. 1 (1961), 361-379 | Wikipedia citation with Project Euclid link (MR 0133191) | http://projecteuclid.org/euclid.bsmsp/1200512173 | 2026-09-24 | vol 1, pp 361-379, 1961 | thm James-Stein; omsources |
| F3 | B. Efron and C. Morris, "Data analysis using Stein's estimator and its generalizations", JASA 70(350) (1975), 311-319 (the batting-average example) | Crossref record | https://doi.org/10.1080/01621459.1975.10479864 | 2026-09-24 | vol 70(350), pp 311-319 | section 2; omsources |
| F4 | N. Metropolis, A. W. Rosenbluth, M. N. Rosenbluth, A. H. Teller and E. Teller, "Equation of state calculations by fast computing machines", J. Chemical Physics 21(6) (1953), 1087-1092 | Crossref record (five authors) | https://doi.org/10.1063/1.1699114 | 2026-09-24 | vol 21(6), pp 1087-1092 | def Metropolis-Hastings; omsources |
| F5 | W. K. Hastings, "Monte Carlo sampling methods using Markov chains and their applications", Biometrika 57(1) (1970), 97-109 | Crossref record | https://doi.org/10.1093/biomet/57.1.97 | 2026-09-24 | vol 57(1), pp 97-109 | def Metropolis-Hastings; omsources |
| F6 | S. Geman and D. Geman, "Stochastic relaxation, Gibbs distributions, and the Bayesian restoration of images", IEEE PAMI 6(6) (1984), 721-741 | Crossref record | https://doi.org/10.1109/TPAMI.1984.4767596 | 2026-09-24 | vol PAMI-6(6), pp 721-741 | def Gibbs sampler; omsources |
| F7 | A. Gelman and D. B. Rubin, "Inference from iterative simulation using multiple sequences", Statistical Science 7(4) (1992): the potential scale reduction R-hat | Crossref record | https://doi.org/10.1214/ss/1177011136 | 2026-09-24 | vol 7(4), 1992 | section 4 (R-hat); omsources |
| F8 | C. J. Geyer, "Practical Markov chain Monte Carlo", Statistical Science 7(4) (1992): initial positive sequence estimator used by firm.bayes.ess | Crossref record | https://doi.org/10.1214/ss/1177011137 | 2026-09-24 | vol 7(4), 1992 | firm.bayes (ess docstring) |

## EXCLUDED

- Robbins 1956 (planned): named only in the Build Stretch field ("the Robbins formula"), no bibliographic claim.
- The platform (50 managers, N(0.5, 0.4^2) true Sharpe ratios, three-year records) is a simulation, not a market fact; seed 203 chosen for a best record of 2.4 as in the hook.

