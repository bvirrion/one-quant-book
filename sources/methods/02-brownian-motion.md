# 2. Brownian Motion — brief and source ledger

## Brief

- **Hook.** A trader places a stop-loss 2% below entry on a stock with 30% volatility and asks the chance it is hit within a month; the answer from continuous monitoring is about double the chance the stock merely ends the month below the stop, and a stop checked only at the close is hit noticeably less often.
- **Sections.** From random walks to Brownian motion; Path properties and the Markov property; The reflection principle and first-passage times; Quadratic variation; The Brownian bridge.
- **Defines.** Brownian motion, Gaussian process, Markov process, strong Markov property, first-passage time, hitting time, Brownian motion with drift, quadratic variation, Brownian bridge.
- **Uses (defined earlier).** martingale, stopping time, filtration, realised volatility, variance, barrier option, Bachelier model.
- **Results (named theorems, not terms).** Donsker's invariance principle; reflection principle and the law of the running maximum; first-passage density with drift; nowhere differentiability of paths (stated); quadratic variation of Brownian motion equals t.
- **Tutorial.** Simulate Brownian paths two ways (increments and bridge refinement), check the square-root scaling, compare the simulated running maximum with the reflection formula, and watch the realised quadratic variation converge to t as the mesh shrinks.
- **Build.** `firm.mcengine` (first stage): seeded Brownian path generation by increments and by Brownian-bridge refinement, correlated d-dimensional paths; Python, C++20 and Rust.
- **Weekend problem.** The stop-loss — named result: the probability that a stop 2% below entry is touched within 21 trading days at 30% volatility, under continuous monitoring and under daily-close monitoring, and the Broadie-Glasserman-Kou barrier shift that reconciles them.
- **Facts to verify.** Bachelier 1900, Théorie de la spéculation; Wiener 1923 construction; Donsker 1951 invariance principle; Broadie, Glasserman and Kou 1997, continuity correction 0.5826 sigma sqrt(dt) (Mathematical Finance); Lévy's work on the running maximum (1948 monograph).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | L. Bachelier, "Théorie de la spéculation", thesis defended 29 March 1900 (Sorbonne; jury Appell, Boussinesq, Poincaré), published in Annales scientifiques de l'É.N.S., 3e série, tome 17 (1900), 21-86 | Numdam | https://www.numdam.org/item/ASENS_1900_3_17__21_0/ | 2026-09-24 | Annales scientifiques de l'É.N.S. 3e série, 17 (1900) 21-86 | omsources |
| F2 | N. Wiener, "Differential-Space", Journal of Mathematics and Physics 2 (1923), 131-174: first construction of Brownian motion as a measure on paths | Wiley Online Library record | https://onlinelibrary.wiley.com/doi/abs/10.1002/sapm192321131 | 2026-09-24 | "Differential-Space - Wiener - 1923 - Journal of Mathematics and Physics" | §1 (Wiener 1923); omsources |
| F3 | M. D. Donsker, "An invariance principle for certain probability limit theorems", Memoirs of the AMS no. 6 (1951), 1-12 | Scientific Research Publishing reference record; Rockefeller digital commons ("Four papers on probability", AMS Memoirs 6) | https://digitalcommons.rockefeller.edu/pamphlets-offprints-and-reprints/77/ | 2026-09-24 | "Memoirs of American Mathematical Society, No. 6" | thm Donsker; omsources |
| F4 | Broadie, Glasserman and Kou, "A continuity correction for discrete barrier options", Mathematical Finance 7(4) (1997), 325-349 | RePEc/IDEAS record | https://ideas.repec.org/a/bla/mathfi/v7y1997i4p325-349.html | 2026-09-24 | "Mathematical Finance, vol. 7(4), pages 325-349" | prop BGK; problem; omsources |
| F5 | The BGK shift constant beta = -zeta(1/2)/sqrt(2 pi) = 0.5826 and the shifted-barrier rule K - beta sigma sqrt(dt) | Almost Sure (G. Lowther), "Discrete barrier approximations", 2023 (secondary, citing BGK 1997) | https://almostsuremath.com/2023/07/01/discrete-barrier-approximations/ | 2026-09-24 | "mean beta = -1/sqrt(2 pi) zeta(1/2) ~ 0.5826"; "K~ = K - beta sigma sqrt(dt)" | prop BGK; problem 7 |
| F6 | I. Karatzas and S. E. Shreve, Brownian Motion and Stochastic Calculus, Springer, 2nd ed. 1991 (GTM 113) | Springer book record | https://link.springer.com/book/10.1007/978-1-4612-0949-2 | 2026-09-24 | GTM 113, 2nd ed. Springer 1991, eBook ISBN 978-1-4612-0949-2 (confirmed by search, Google Books record id ATNy_Zg3PSsC) | thm strong Markov (admitted); omsources |

## EXCLUDED

- Lévy (1948 monograph) on the running maximum: not cited in the text.
- Reflection, quadratic variation, bridge crossing probability, BGK numbers: derived or simulated in the chapter, asserted in test_solutions.py.

