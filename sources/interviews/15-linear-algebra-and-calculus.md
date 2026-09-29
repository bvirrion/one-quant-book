# 15. Linear Algebra and Calculus — brief and source ledger

## Brief

- **Hook.** A risk system rejects the morning's correlation matrix: one eigenvalue is minus 0.02. The quant on call is asked, before touching code, why three pairwise correlations that each look reasonable can be impossible together, and what the nearest valid matrix is.
- **Sections.** Eigenvalues, definiteness and correlation matrices; Projections, least squares and the geometry of regression; Integrals, series and expansions that interviews reach for; Optimisation with constraints.
- **Defines.** none (the chapter uses the vocabulary of Books 1-17, listed below).
- **Uses (defined earlier).** covariance matrix (B4.22), principal component analysis (B4.22), Cholesky factorisation (B4.25), singular value decomposition (B4.25), ordinary least squares (B4.16), eigenvalue clipping (B4.22), minimum-variance portfolio (B4.22), sanity check (ch5).
- **Question bank.** 13 questions, 4/5/4. Families: feasibility of a three-by-three correlation matrix (the range of the third correlation, numeric); eigenvalues of structured matrices (equicorrelation, rank one plus identity); positive definiteness tests; projection and residual questions; the minimum-variance portfolio of two assets (numeric); integrals by symmetry or a trick (Gaussian moments, a Laplace transform); series and expansions (the sum of a geometric-arithmetic series, a Taylor error); a Lagrangian with one constraint. Roles: researcher 6, bank 3, trader 2, mle 1, risk 1. Firms: systematic fund 4, bank 3, market maker 2, any 4.
- **Facts to verify.** none external: all answers derived; Higham 2002 (IMA J. Numer. Anal.) on the nearest correlation matrix as the method source.
- **Data.** Figures: one schematic (the feasible region of the third correlation as a function of the other two, drawn from the determinant condition; figdata from fig_iv_corr.py). Code: iv_linalg.py (sympy for symbolic eigenvalues and integrals; numpy checks; nearest correlation matrix by alternating projections against the printed value).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Higham, Computing the nearest correlation matrix - a problem from finance, IMA Journal of Numerical Analysis 22(3), 329-343, 2002 | Crossref | https://api.crossref.org/works/10.1093/imanum/22.3.329 | 2026-09-29 | title, journal, volume, issue, pages | section 1; omsources |

## EXCLUDED

