# 23. Convex Optimisation — brief and source ledger

## Brief

- **Hook.** At 15:45 an optimiser must turn 2,000 return forecasts into orders under sector-neutrality, turnover and position limits before the close. It answers in 40 milliseconds; on the day the limits contradict one another it says so, and returns the proof.
- **Sections.** Convex sets, functions and problems; Duality; Optimality conditions; Quadratic and second-order cone programmes; What solvers actually do.
- **Defines.** convex set, convex function, convex optimisation problem, Lagrangian, dual problem, strong duality, Slater's condition, shadow price, Karush--Kuhn--Tucker conditions, linear programme, quadratic programme, second-order cone programme, semidefinite programme, interior-point method, infeasibility certificate, nearest correlation matrix.
- **Uses (defined earlier).** minimum-variance portfolio, covariance matrix, factor model, tracking error, leverage, notional turnover.
- **Results (named theorems, not terms).** a local minimum of a convex problem is global; weak duality; strong duality under Slater's condition; KKT conditions are necessary and sufficient for convex problems with Slater; Farkas' lemma and infeasibility certificates; tracking-error and risk limits as second-order cone constraints; a 3/2-power impact cost as a cone constraint.
- **Tutorial.** Formulate a long-short portfolio with sector neutrality, gross-exposure and position limits as a quadratic programme, solve it, verify the KKT conditions, and read each constraint's multiplier as a shadow price; make the limits inconsistent and read the certificate.
- **Build.** `firm.portopt`: portfolio optimiser (a formulation layer for budget, neutrality, box, gross-exposure, turnover and tracking-error constraints; an interior-point QP/SOCP solver of its own and an ADMM fallback; KKT residuals, dual variables and infeasibility diagnostics in the report); Python.
- **Weekend problem.** The constraint that cost the most — named result: the shadow price of the turnover limit (expected return given up per 1% of turnover) and the ranking of all constraints by the return they cost.
- **Facts to verify.** Karush 1939 (Chicago MSc thesis); Kuhn and Tucker 1951 (Berkeley Symposium); Markowitz 1952 (Journal of Finance); Dantzig 1947 simplex; Karmarkar 1984 (Combinatorica); Nesterov and Nemirovskii 1994 interior-point polynomial algorithms; Boyd and Vandenberghe 2004, Convex Optimization; Higham 2002 (IMA J. Numerical Analysis) nearest correlation matrix; Stellato et al. 2020 OSQP (Mathematical Programming Computation); Lobo, Vandenberghe, Boyd and Lebret 1998 (Linear Algebra and its Applications) SOCP applications.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | W. Karush, Minima of Functions of Several Variables with Inequalities as Side Constraints, MSc thesis, Dept. of Mathematics, University of Chicago, 1939; H. W. Kuhn and A. W. Tucker, "Nonlinear programming", Proc. 2nd Berkeley Symposium (1951), 481-492 | Wikipedia (Karush-Kuhn-Tucker conditions) citations with Project Euclid link | http://projecteuclid.org/euclid.bsmsp/1200500249 | 2026-09-24 | Kuhn-Tucker pp 481-492, 1951; Karush thesis 1939 (catalogue http://pi.lib.uchicago.edu/1001/cat/bib/4111654) | def KKT; omsources |
| F2 | H. Markowitz, "Portfolio selection", Journal of Finance 7(1) (1952), 77-91 | Crossref record | https://doi.org/10.1111/j.1540-6261.1952.tb01525.x | 2026-09-24 | vol 7(1), pp 77-91 | omsources |
| F3 | N. Karmarkar, "A new polynomial-time algorithm for linear programming", Combinatorica 4(4) (1984), 373-395 | Crossref record | https://doi.org/10.1007/BF02579150 | 2026-09-24 | vol 4(4), pp 373-395 | section 5; omsources |
| F4 | S. Mehrotra, "On the implementation of a primal-dual interior point method", SIAM J. Optimization 2(4) (1992), 575-601 | Crossref record | https://doi.org/10.1137/0802028 | 2026-09-24 | vol 2(4), pp 575-601 | section 5; firm.portopt; omsources |
| F5 | Y. Nesterov and A. Nemirovskii, Interior-Point Polynomial Algorithms in Convex Programming, SIAM, 1994 | Crossref record | https://doi.org/10.1137/1.9781611970791 | 2026-09-24 | SIAM book, 1994 | section 5; omsources |
| F6 | S. Boyd and L. Vandenberghe, Convex Optimization, Cambridge University Press, 2004 | Crossref record | https://doi.org/10.1017/CBO9780511804441 | 2026-09-24 | CUP, 2004 | omsources |
| F7 | M. S. Lobo, L. Vandenberghe, S. Boyd and H. Lebret, "Applications of second-order cone programming", Linear Algebra and its Applications 284(1-3) (1998), 193-228 | Crossref record | https://doi.org/10.1016/S0024-3795(98)10032-0 | 2026-09-24 | vol 284, pp 193-228 | section 4; omsources |
| F8 | N. J. Higham, "Computing the nearest correlation matrix: a problem from finance", IMA J. Numerical Analysis 22(3) (2002), 329-343 | Crossref record | https://doi.org/10.1093/imanum/22.3.329 | 2026-09-24 | vol 22(3), pp 329-343 | def nearest correlation matrix; firm.portopt; omsources |
| F9 | B. Stellato, G. Banjac, P. Goulart, A. Bemporad and S. Boyd, "OSQP: an operator splitting solver for quadratic programs", Mathematical Programming Computation 12(4) (2020), 637-672 | Crossref record (five authors) | https://doi.org/10.1007/s12532-020-00179-2 | 2026-09-24 | vol 12(4), pp 637-672 | section 5; firm.portopt admm; omsources |

## EXCLUDED

- Dantzig 1947 (planned): not cited.
- The portfolio (200 stocks, forecasts, limits) is a simulation. Brief deviation: 200 stocks, not 2,000, and no solve-time claim (the Python solver needs seconds; the hook states no timing).
- Solver residuals below 1e-9 depend on BLAS operation order and are floored in the chart data.

