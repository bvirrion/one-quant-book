# 13. Resampling — brief and source ledger

## Brief

- **Hook.** A strategy's five-year Sharpe ratio is 1.1 and the head of desk asks for a 95% interval before doubling its capital. Resampling days independently gives one interval; resampling months of days, which keeps the volatility clusters together, gives a wider one, and only the second is honest.
- **Sections.** The bootstrap; Dependent data: block and stationary bootstraps; Permutation tests; The jackknife; Bootstrapping the reality check.
- **Defines.** bootstrap, empirical distribution function, bootstrap percentile interval, coverage probability, moving-block bootstrap, stationary bootstrap, permutation test, exchangeability, jackknife.
- **Uses (defined earlier).** estimator, standard error, Sharpe ratio, p-value, Reality Check, family-wise error rate, HAC estimator.
- **Results (named theorems, not terms).** consistency of the bootstrap for smooth functionals (stated); failure of the bootstrap for the maximum (example); stationary bootstrap is stationary; optimal block length rate n^{1/3} (Politis-White, stated); exactness of permutation tests under exchangeability; jackknife bias correction removes the O(1/n) term.
- **Tutorial.** Bootstrap the Sharpe ratio of a volatility-clustered strategy with iid, moving-block and stationary bootstraps; measure each interval's coverage over many simulated histories.
- **Build.** `firm.resample`: iid, moving-block and stationary bootstrap index generators, automatic block length, permutation tests, jackknife; seeded and vectorised; Python.
- **Weekend problem.** The interval that was too narrow — named result: the coverage of the nominal 95% iid and stationary-bootstrap intervals for the Sharpe ratio of a strategy with volatility clustering.
- **Facts to verify.** Efron 1979 (Annals of Statistics); Künsch 1989 (Annals of Statistics) block bootstrap; Politis and Romano 1994 (JASA) stationary bootstrap; Politis and White 2004 (Econometric Reviews) block length; Patton, Politis and White 2009 correction; Quenouille 1949 / Tukey 1958 jackknife; Fisher 1935 permutation test (The Design of Experiments).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | B. Efron, "Bootstrap methods: another look at the jackknife", Annals of Statistics 7(1) (1979) | Crossref record | https://doi.org/10.1214/aos/1176344552 | 2026-09-24 | vol 7(1), 1979 | def bootstrap; omsources |
| F2 | H. R. Kunsch, "The jackknife and the bootstrap for general stationary observations", Annals of Statistics 17(3) (1989): the moving-block bootstrap | Crossref record | https://doi.org/10.1214/aos/1176347265 | 2026-09-24 | vol 17(3), 1989 | def moving-block bootstrap; omsources |
| F3 | D. N. Politis and J. P. Romano, "The stationary bootstrap", JASA 89(428) (1994), 1303-1313 | Crossref record | https://doi.org/10.1080/01621459.1994.10476870 | 2026-09-24 | vol 89(428), pp 1303-1313 | def stationary bootstrap; omsources |
| F4 | D. N. Politis and H. White, "Automatic block-length selection for the dependent bootstrap", Econometric Reviews 23(1) (2004), 53-70 | Crossref record | https://doi.org/10.1081/ETC-120028836 | 2026-09-24 | vol 23(1), pp 53-70 | section 2 (block length); firm.resample; omsources |
| F5 | A. Patton, D. N. Politis and H. White, "Correction to 'Automatic block-length selection for the dependent bootstrap'", Econometric Reviews 28(4) (2009), 372-375 | Crossref record | https://doi.org/10.1080/07474930802459016 | 2026-09-24 | vol 28(4), pp 372-375 | section 2; firm.resample; omsources |
| F6 | M. H. Quenouille, "Approximate tests of correlation in time-series", JRSS B 11(1) (1949), 68-84 (origin of the jackknife bias correction) | Crossref record | https://doi.org/10.1111/j.2517-6161.1949.tb00023.x | 2026-09-24 | vol 11(1), pp 68-84 | omsources |

## EXCLUDED

- Tukey 1958 and Fisher 1935 (planned): not cited in the text.
- The Politis-White constants (D_SB = 2 g(0)^2, D_CB = (4/3) g(0)^2, flat-top window, K_n = max(5, sqrt(log10 n)), c = 2) are implemented from the published method; the acceptance test checks the AR(1) closed form.
- The volatility seller and the permutation pairs are simulations, not market facts. Brief deviation: the hook strategy is a volatility seller (P&L = premium - squared return), because a constant-mean strategy with clustered volatility has an iid-correct Sharpe interval; the regime-switching alternative was tried and rejected (automatic block rule picks 1-2 days, coverage 77% -> 80%).

