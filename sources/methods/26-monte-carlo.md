# 26. Monte Carlo — brief and source ledger

## Brief

- **Hook.** The overnight batch values 40,000 path-dependent trades with 100,000 paths each; the standard error on the book is 80,000 dollars and the risk manager wants it under 20,000 by tomorrow, without sixteen times the machines.
- **Sections.** Estimators and generators; Variance reduction and importance sampling; Low-discrepancy sequences; Discretisation and multilevel methods.
- **Defines.** Monte Carlo method, variance reduction, pseudo-random number generator, counter-based generator, inverse transform sampling, antithetic variates, control variate, stratified sampling, importance sampling, low-discrepancy sequence, Sobol sequence, quasi-Monte Carlo, randomised quasi-Monte Carlo, Brownian bridge construction, strong order of convergence, weak order of convergence, Milstein scheme, multilevel Monte Carlo.
- **Uses (defined earlier).** Brownian bridge, Euler--Maruyama scheme, geometric Brownian motion, Radon--Nikodym derivative, change of measure, standard error, central limit theorem (result), barrier option, square-root process.
- **Results (named theorems, not terms).** central limit theorem for the Monte Carlo estimator and the cost-variance product; optimal control-variate coefficient and its variance reduction 1 - rho^2; zero-variance importance density; Koksma-Hlawka inequality; strong order 1/2 and weak order 1 of Euler; strong order 1 of Milstein; Giles' multilevel complexity theorem.
- **Tutorial.** Value an arithmetic-average payoff on geometric Brownian motion with plain Monte Carlo, antithetic variates, the geometric-average control variate, and Sobol points with a Brownian-bridge construction; plot error against cost on log-log axes.
- **Build.** `firm.mcengine` (third stage): variance-reduction hooks (antithetic, control variates), Sobol generator with Joe-Kuo direction numbers and Owen scrambling, Brownian-bridge path construction, counter-based Philox streams, multilevel driver; Python, C++20 and Rust.
- **Weekend problem.** Sixteen times fewer machines — named result: the variance-reduction factor of control variate plus randomised QMC on the book's representative trade, and whether it meets the 20,000-dollar target at today's cost.
- **Facts to verify.** Metropolis and Ulam 1949 (JASA) 'The Monte Carlo method'; Boyle 1977 (J. Financial Economics) first Monte Carlo option valuation; Matsumoto and Nishimura 1998 MT19937 (ACM TOMACS); Salmon, Moraes, Dror and Shaw 2011 Philox (SC11); O'Neill 2014 PCG; NumPy default_rng uses PCG64 (NumPy documentation); Sobol 1967; Joe and Kuo 2008 direction numbers and their licence; Owen 1995 scrambling; Kemna and Vorst 1990 (J. Banking and Finance) geometric control variate; Giles 2008 (Operations Research) multilevel Monte Carlo; Glasserman 2003, Monte Carlo Methods in Financial Engineering; Kloeden and Platen 1992.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | N. Metropolis and S. Ulam, "The Monte Carlo method", JASA 44(247) (1949), 335-341 | Crossref record | https://doi.org/10.1080/01621459.1949.10483310 | 2026-09-24 | vol 44(247), pp 335-341 | omsources |
| F2 | P. P. Boyle, "Options: a Monte Carlo approach", J. Financial Economics 4(3) (1977), 323-338 | Crossref record | https://doi.org/10.1016/0304-405X(77)90005-8 | 2026-09-24 | vol 4(3), pp 323-338 | omsources |
| F3 | M. Matsumoto and T. Nishimura, "Mersenne twister", ACM TOMACS 8(1) (1998), 3-30 | Crossref record | https://doi.org/10.1145/272991.272995 | 2026-09-24 | vol 8(1), pp 3-30 | def PRNG; omsources |
| F4 | J. K. Salmon, M. A. Moraes, R. O. Dror and D. E. Shaw, "Parallel random numbers: as easy as 1, 2, 3", SC11 (2011), 1-12 | Crossref record (title + subtitle, four authors) | https://doi.org/10.1145/2063384.2063405 | 2026-09-24 | title "Parallel random numbers", subtitle "as easy as 1, 2, 3" | def counter-based generator; omsources |
| F5 | M. E. O'Neill, PCG: a family of simple fast space-efficient statistically good algorithms for random number generation, Harvey Mudd College report HMC-CS-2014-0905, September 2014 | author's page (BibTeX entry) | https://www.pcg-random.org/paper.html | 2026-09-24 | number = "HMC-CS-2014-0905", year = "2014" | def PRNG; omsources |
| F6 | NumPy: default_rng constructs a Generator with the default BitGenerator (PCG64); numpy.random.Philox is the Philox (4x64) counter-based generator | NumPy v2.5 manual | https://numpy.org/doc/stable/reference/random/generator.html | 2026-09-24 | "Construct a new Generator with the default BitGenerator (PCG64)"; Philox page: "Container for the Philox (4x64) pseudo-random number generator" (https://numpy.org/doc/stable/reference/random/bit_generators/philox.html) | def PRNG; section 1 |
| F7 | I. M. Sobol', "On the distribution of points in a cube and the approximate evaluation of integrals", USSR Comput. Math. Math. Phys. 7(4) (1967), 86-112 | Crossref record | https://doi.org/10.1016/0041-5553(67)90144-9 | 2026-09-24 | vol 7(4), pp 86-112 | def Sobol sequence; omsources |
| F8 | S. Joe and F. Y. Kuo, "Constructing Sobol sequences with better two-dimensional projections", SIAM J. Sci. Comput. 30(5) (2008), 2635-2654; direction numbers new-joe-kuo-6.21201 under a BSD-style licence; published first 10 points in 3 dimensions of sobol.cc | Crossref record; authors' Sobol page and licence file | https://web.maths.unsw.edu.au/~fkuo/sobol/ | 2026-09-24 | page: "covered by this BSD-style licence"; "./sobol 10 3 new-joe-kuo-6.21201 gives the output 0 0 0 0.5 0.5 0.5 0.75 0.25 0.25 ..."; DOI 10.1137/070709359 | def Sobol sequence; build; tests; omsources |
| F9 | A. B. Owen, "Randomly permuted (t,m,s)-nets and (t,s)-sequences", Lecture Notes in Statistics 106 (1995), 299-317 | Crossref record | https://doi.org/10.1007/978-1-4612-2552-2_19 | 2026-09-24 | pp 299-317, 1995 | def RQMC; omsources |
| F10 | B. Moskowitz and R. E. Caflisch, "Smoothness and dimension reduction in quasi-Monte Carlo methods", Math. Comput. Modelling 23(8-9) (1996), 37-54 | Crossref record | https://doi.org/10.1016/0895-7177(96)00038-6 | 2026-09-24 | vol 23(8-9), pp 37-54 | def Brownian bridge construction; omsources |
| F11 | A. G. Z. Kemna and A. C. F. Vorst, "A pricing method for options based on average asset values", J. Banking and Finance 14(1) (1990), 113-129 | Crossref record | https://doi.org/10.1016/0378-4266(90)90039-5 | 2026-09-24 | vol 14(1), pp 113-129 | section 2 (geometric control); omsources |
| F12 | M. B. Giles, "Multilevel Monte Carlo path simulation", Operations Research 56(3) (2008), 607-617 | Crossref record | https://doi.org/10.1287/opre.1070.0496 | 2026-09-24 | vol 56(3), pp 607-617 | def MLMC; proposition; omsources |
| F13 | P. Glasserman, Monte Carlo Methods in Financial Engineering, Springer, 2003 | Crossref record | https://doi.org/10.1007/978-0-387-21617-1 | 2026-09-24 | Springer, 2003 | omsources |
| F14 | P. E. Kloeden and E. Platen, Numerical Solution of Stochastic Differential Equations, Springer, 1992 | Crossref record | https://doi.org/10.1007/978-3-662-12616-5 | 2026-09-24 | Springer, 1992 | proposition (orders); omsources |
| F15 | G. N. Milstein, "Approximate integration of stochastic differential equations", Theory of Probability and its Applications 19(3) (1975; English translation), 557-562 | Crossref record | https://doi.org/10.1137/1119062 | 2026-09-24 | vol 19(3), pp 557-562, 1975 | def Milstein scheme; omsources |
| F16 | P. J. Acklam, "An algorithm for computing the inverse normal cumulative distribution function" (updated 2004-05-04): relative error below 1.15e-9; coefficients as used in norm_ppf | archived web note | https://web.archive.org/web/2007id_/http://home.online.no/~pjacklam/notes/invnorm/ | 2026-09-24 | "relative error has an absolute value less than 1.15e-9 in the entire region"; coefficients -3.969683028665376e+01 and 7.784695709041462e-03 present | section 1; omsources |

## EXCLUDED

- Nothing excluded. The hook's batch (40,000 trades, 100,000 paths, 80,000-dollar standard error) is an illustrative scenario, not a claim about a firm.

## Brief deviations

- Tutorial "error against cost" uses the number of paths (payoff evaluations) as the cost; generation overhead (scrambling, Philox vs PCG) is not timed, since Python timings would not transfer to the production engine; the text says so.
- MLMC is demonstrated on a European call with Milstein corrections (beta = 2 > gamma = 1), not on the Asian trade.
- Twins (C++20, Rust) cover Philox, Sobol (first eight dimensions, embedded) and Owen scrambling; the multilevel driver and estimators are Python only.
