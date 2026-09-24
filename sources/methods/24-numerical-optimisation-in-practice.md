# 24. Numerical Optimisation in Practice — brief and source ledger

## Brief

- **Hook.** A calibration that has converged in 200 milliseconds every morning for a year lands one Monday on parameters that fit the quotes just as well as Friday's and mean something entirely different. The objective had two valleys, and the optimiser had always started in the same one.
- **Sections.** First-order methods; Newton, quasi-Newton and nonlinear least squares; Operator splitting; Stochastic gradients; Non-convex calibration and its traps.
- **Defines.** gradient descent, line search, momentum method, Nesterov acceleration, Newton's method, quasi-Newton method, BFGS method, nonlinear least squares, Gauss--Newton method, Levenberg--Marquardt algorithm, proximal operator, proximal gradient method, alternating direction method of multipliers, stochastic gradient descent, calibration, identifiability, multistart.
- **Uses (defined earlier).** convex function, Karush--Kuhn--Tucker conditions, quadratic programme, lasso, elastic net, nearest correlation matrix, maximum likelihood estimator, Hawkes process, excitation kernel, regularisation, Fisher information.
- **Results (named theorems, not terms).** convergence rates of gradient descent: linear with rate (1 - 1/cond) for strongly convex functions, O(1/k) and O(1/k^2) with acceleration; local quadratic convergence of Newton's method; Wolfe conditions guarantee a positive-definite BFGS update; ADMM convergence for convex problems (stated); Robbins-Monro step-size conditions.
- **Tutorial.** Fit a two-exponential kernel to a decaying autocorrelation from 100 random starts with L-BFGS and Levenberg-Marquardt, histogram the end points, exhibit the degenerate valley, and add a penalty toward yesterday's parameters; then solve the nearest correlation matrix by ADMM and by alternating projections.
- **Build.** `firm.optim`: optimisation and calibration harness (parameter transforms and bounds, multistart, Levenberg-Marquardt, L-BFGS, proximal gradient and ADMM of its own, a Tikhonov penalty toward the previous fit, convergence and identifiability diagnostics logged per run); Python.
- **Weekend problem.** The Monday the fit moved — named result: the day-to-day parameter jump with and without the penalty toward yesterday, and the fit error the penalty costs.
- **Facts to verify.** Cauchy 1847 gradient method; Nesterov 1983 (Soviet Math. Doklady); Levenberg 1944; Marquardt 1963 (SIAM J.); Broyden, Fletcher, Goldfarb and Shanno 1970; Liu and Nocedal 1989 (Mathematical Programming) L-BFGS; Robbins and Monro 1951 (Annals of Math. Statistics); Beck and Teboulle 2009 (SIAM J. Imaging Sciences) FISTA; Boyd, Parikh, Chu, Peleato and Eckstein 2011 ADMM monograph; Kingma and Ba 2015 Adam (ICLR); Nocedal and Wright, Numerical Optimization (2nd ed. 2006).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | K. Levenberg, "A method for the solution of certain non-linear problems in least squares", Quarterly of Applied Mathematics 2(2) (1944), 164-168 | Crossref record | https://doi.org/10.1090/qam/10666 | 2026-09-24 | vol 2(2), pp 164-168 | def LM; omsources |
| F2 | D. W. Marquardt, "An algorithm for least-squares estimation of nonlinear parameters", J. SIAM 11(2) (1963), 431-441 | Crossref record | https://doi.org/10.1137/0111030 | 2026-09-24 | vol 11(2), pp 431-441 | def LM; omsources |
| F3 | D. C. Liu and J. Nocedal, "On the limited memory BFGS method for large scale optimization", Mathematical Programming 45(1-3) (1989), 503-528 | Crossref record | https://doi.org/10.1007/BF01589116 | 2026-09-24 | vol 45, pp 503-528 | def BFGS (L-BFGS); omsources |
| F4 | H. Robbins and S. Monro, "A stochastic approximation method", Annals of Mathematical Statistics 22(3) (1951), 400-407 | Crossref record | https://doi.org/10.1214/aoms/1177729586 | 2026-09-24 | vol 22(3), pp 400-407 | section 5; omsources |
| F5 | A. Beck and M. Teboulle, "A fast iterative shrinkage-thresholding algorithm for linear inverse problems", SIAM J. Imaging Sciences 2(1) (2009), 183-202 | Crossref record | https://doi.org/10.1137/080716542 | 2026-09-24 | vol 2(1), pp 183-202 | def proximal gradient (FISTA); omsources |
| F6 | S. Boyd, N. Parikh, E. Chu, B. Peleato and J. Eckstein, "Distributed optimization and statistical learning via the alternating direction method of multipliers", Foundations and Trends in Machine Learning 3(1) (2011), 1-122 | Crossref record (five authors) | https://doi.org/10.1561/2200000016 | 2026-09-24 | vol 3(1), pp 1-122 | def ADMM; omsources |
| F7 | D. P. Kingma and J. Ba, "Adam: a method for stochastic optimization", arXiv:1412.6980 (2014) | arXiv abstract page | https://arxiv.org/abs/1412.6980 | 2026-09-24 | title "Adam: A Method for Stochastic Optimization", author Kingma | section 5; omsources |
| F8 | J. Nocedal and S. J. Wright, Numerical Optimization, 2nd ed., Springer, 2006 | Crossref record | https://doi.org/10.1007/978-0-387-40065-5 | 2026-09-24 | Springer, 2006 | omsources |
| F9 | BFGS 1970: C. G. Broyden, IMA J. Applied Mathematics 6(1), 76-90; R. Fletcher, The Computer Journal 13(3), 317-322; D. Goldfarb, Mathematics of Computation 24(109), 23-26; D. F. Shanno, Mathematics of Computation 24(111), 647-656 | Crossref records | https://doi.org/10.1093/comjnl/13.3.317 | 2026-09-24 | four 1970 papers (DOIs 10.1093/imamat/6.1.76, 10.1093/comjnl/13.3.317, 10.1090/S0025-5718-1970-0258249-6, 10.1090/S0025-5718-1970-0274029-X) | def BFGS |

## EXCLUDED

- Cauchy 1847 and Nesterov 1983 (planned): Nesterov appears only in the method's name; no bibliographic claim.
- The calibration is simulated (true kernel 0.6, 3, 60 days; noise 0.01). Brief deviation: the hook describes the flat valley (tau2 56.8 -> 87.6 days with an equal fit) rather than a switch between the two mirror valleys, which the fixed start never produced; the mirror valley appears in the multistart.

