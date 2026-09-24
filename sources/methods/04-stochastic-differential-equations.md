# 4. Stochastic Differential Equations — brief and source ledger

## Brief

- **Hook.** At 02:00 the overnight risk run stops: a square-root variance process stepped with plain Euler went negative on 3% of its paths and the code took the square root of a negative number. The model was fine; the scheme and the Feller condition were the problem.
- **Sections.** Existence, uniqueness and the Euler scheme; The workhorse diffusions: geometric, mean-reverting, square-root; Generators and the Kolmogorov equations; Feynman--Kac.
- **Defines.** stochastic differential equation, strong solution, weak solution, Euler--Maruyama scheme, geometric Brownian motion, mean reversion, Ornstein--Uhlenbeck process, half-life, square-root process, Feller condition, infinitesimal generator, Kolmogorov backward equation, Kolmogorov forward equation, Fokker--Planck equation, stationary distribution.
- **Uses (defined earlier).** Brownian motion, Itô's formula (result), Itô process, Markov process, martingale, local martingale, curve fly.
- **Results (named theorems, not terms).** existence and uniqueness under Lipschitz and linear-growth conditions; explicit solutions and transition laws of GBM and OU; noncentral chi-square law of the square-root process; Dynkin's formula; Feynman-Kac formula (with discounting).
- **Tutorial.** Sample Ornstein-Uhlenbeck and square-root paths exactly (Gaussian and noncentral chi-square transitions) and with Euler-Maruyama; count negative values against the Feller ratio and the step; check the stationary laws against the Kolmogorov forward equation.
- **Build.** `firm.mcengine` (second stage): SDE stepping (Euler-Maruyama, exact OU, exact square-root, full-truncation Euler) on the stage-one paths; Python, C++20 and Rust.
- **Weekend problem.** The NaN in the overnight run — named result: the Feller ratio of the desk's calibrated variance process and the share of daily-step Euler paths that turn negative within a year, against zero for the exact scheme and the full-truncation fix.
- **Facts to verify.** Feller 1951 (Annals of Mathematics) two singular diffusion problems; Cox, Ingersoll and Ross 1985 (Econometrica) square-root process; Uhlenbeck and Ornstein 1930 (Physical Review); Kac 1949 / Feynman 1948 (Feynman-Kac); Lord, Koekkoek and van Dijk 2010 full truncation (Quantitative Finance); Kolmogorov 1931 analytical methods paper.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | W. Feller, "Two singular diffusion problems", Annals of Mathematics 54 (1951), 173-182: boundary classification of the square-root diffusion | Scientific Research Publishing reference record; Semantic Scholar | https://www.scirp.org/reference/referencespapers?referenceid=2741095 | 2026-09-24 | "Annals of Mathematics, 54, 173-182" | thm Feller; omsources |
| F2 | Cox, Ingersoll and Ross, "A theory of the term structure of interest rates", Econometrica 53(2) (1985), 385-407: the square-root short rate and its noncentral chi-square transition | RePEc/IDEAS record | https://ideas.repec.org/a/ecm/emetrp/v53y1985i2p385-407.html | 2026-09-24 | "Econometrica, vol. 53(2), pages 385-407" | thm Feller (transition law); omsources |
| F3 | G. E. Uhlenbeck and L. S. Ornstein, "On the theory of the Brownian motion", Physical Review 36(5) (1930), 823-841 | NASA ADS record 1930PhRv...36..823U | https://ui.adsabs.harvard.edu/abs/1930PhRv...36..823U/abstract | 2026-09-24 | Phys. Rev. 36, 823 (1930) | omsources |
| F4 | M. Kac, "On distributions of certain Wiener functionals", Transactions of the AMS 65 (1949), 1-13 (the Feynman-Kac formula) | AMS journal PDF | https://www.ams.org/journals/tran/1949-065-01/S0002-9947-1949-0027960-X/S0002-9947-1949-0027960-X.pdf | 2026-09-24 | Trans. AMS 65 (1949) 1-13 | thm Feynman-Kac; omsources |
| F5 | R. Lord, R. Koekkoek and D. van Dijk, "A comparison of biased simulation schemes for stochastic volatility models", Quantitative Finance 10(2) (2010), 177-194: introduces the full truncation scheme | EconPapers record | https://econpapers.repec.org/article/tafquantf/v_3a10_3ay_3a2010_3ai_3a2_3ap_3a177-194.htm | 2026-09-24 | "introduce the new full truncation scheme"; QF 10(2) 177-194 | §2 (full truncation); omsources |
| F6 | Karatzas and Shreve (1991), §5.2: existence and uniqueness under Lipschitz conditions | as ch. 2 F6 / ch. 3 F4 | https://books.google.com/books/about/Brownian_Motion_and_Stochastic_Calculus.html?id=ATNy_Zg3PSsC | 2026-09-24 | 2nd edition 1991 | partial proof |

## EXCLUDED

- Feynman 1948 and Kolmogorov 1931 (planned): not cited in the text.
- Yamada-Watanabe (uniqueness for Hölder-1/2 coefficients): named as an argument, no citation needed beyond Karatzas-Shreve.
- All numbers (Feller ratios, failure shares, stationary masses, bond price) are computed in the chapter's code and asserted in test_solutions.py.

