# 22. Trees and Finite-Difference Pricers in Practice — brief and source ledger

## Brief

- **Hook.** A pricer returns 5.4817 for an American put with 200 time steps and 5.4839 with 201; the trader asks which to trust, and the answer is neither.
- **Sections.** The pricing equation on a grid; Discrete dividends and jump conditions; Barriers and grid alignment; American exercise; Accuracy against speed.
- **Defines.** trinomial tree, jump condition, payoff smoothing, Brennan--Schwartz algorithm.
- **Uses (defined earlier).** theta scheme, Crank--Nicolson scheme, Rannacher start-up, stability (Book 4 ch. 27), Richardson extrapolation (Book 4 ch. 25 or 27), binomial model, Cox--Ross--Rubinstein tree (ch. 2), escrowed dividend model (ch. 5), exercise boundary (ch. 6), barrier option (Book 2 ch. 19).
- **Tutorial.** Build a Crank-Nicolson pricer on a stretched log-spot grid with Rannacher start-up, discrete-dividend jump conditions and American exercise by Brennan-Schwartz; plot error against run time for the tree and the grid.
- **Build.** `firm.fdpricer`: one-dimensional finite-difference pricing engine (Python, C++20, Rust): non-uniform grids, Crank-Nicolson with Rannacher start-up, dividends, barriers, American exercise.
- **Weekend problem.** Neither 200 nor 201 — named result: the grid size and run time at which the American put is within 0.1 cent, for the tree and for the grid, and the speed-up of the grid.
- **Facts to verify.** Brennan-Schwartz 1977 JF; Rannacher 1984; Pooley, Vetzal, Forsyth 2003 convergence remedies; Tavella-Randall 2000 book.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Brennan and Schwartz, "The valuation of American put options", Journal of Finance 32(2) (1977) 449-462 (the Crossref record also lists Merton, whose comment appears in the same issue) | Crossref record 10.1111/j.1540-6261.1977.tb03284.x | https://api.crossref.org/works/10.1111/j.1540-6261.1977.tb03284.x | 2026-09-24 | Crossref metadata | def Brennan-Schwartz algorithm, omsources |
| F2 | Rannacher, "Finite element solution of diffusion problems with irregular data", Numerische Mathematik 43(2) (1984) 309-327 | Crossref record 10.1007/BF01390130 | https://api.crossref.org/works/10.1007/BF01390130 | 2026-09-24 | Crossref metadata | sec. the pricing equation, omsources |
| F3 | Pooley, Vetzal and Forsyth, "Convergence remedies for non-smooth payoffs in option pricing", Journal of Computational Finance 6(4) (2003) 25-40 | Crossref record 10.21314/JCF.2003.101 | https://api.crossref.org/works/10.21314/JCF.2003.101 | 2026-09-24 | Crossref metadata | def payoff smoothing, omsources |
| F4 | Tavella and Randall, Pricing Financial Instruments: The Finite Difference Method (Wiley) | Crossref record of a Wilmott review, 10.1002/wilm.42820030318 | https://api.crossref.org/works/10.1002/wilm.42820030318 | 2026-09-24 | Crossref metadata (review title) | omsources |

## EXCLUDED

- Boyle (1986) on the three-jump (trinomial) process: no fetchable record; the trinomial tree is presented from its construction and not attributed.
- Run times: machine-dependent; the chapter compares work in node updates, which the tests reproduce, and states measured times only qualitatively.
