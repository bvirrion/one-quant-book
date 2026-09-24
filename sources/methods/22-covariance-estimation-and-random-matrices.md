# 22. Covariance Estimation and Random Matrices — brief and source ledger

## Brief

- **Hook.** A minimum-variance portfolio of 500 stocks built from two years of daily returns promises a volatility of 6%; held for the next year it runs at 10%. Nothing broke: with 500 assets and 500 days the sample covariance matrix is mostly noise.
- **Sections.** The sample covariance matrix in high dimension; The eigenvalue law of pure noise; Linear and nonlinear shrinkage; Eigenvalue clipping; Factor-structured covariances.
- **Defines.** covariance matrix, sample covariance matrix, principal component analysis, Marchenko--Pastur law, spiked covariance model, linear shrinkage, nonlinear shrinkage, rotation-equivariant estimator, eigenvalue clipping, factor model, minimum-variance portfolio.
- **Uses (defined earlier).** estimator, shrinkage estimator, James--Stein estimator, variance, tracking error, Sharpe ratio.
- **Results (named theorems, not terms).** Marchenko-Pastur law and its edges (1 +- sqrt(q))^2; BBP phase transition for a spike (stated); in-sample risk of the sample minimum-variance portfolio is biased down by (1 - q), out-of-sample risk up by 1 / (1 - q) (stated and checked); Ledoit-Wolf optimal linear shrinkage intensity; oracle eigenvalues of a rotation-equivariant estimator.
- **Tutorial.** Generate returns from a known factor covariance with 200 assets and 500 days; compare sample eigenvalues with the Marchenko-Pastur law; compare the out-of-sample risk of minimum-variance portfolios from the sample, linear shrinkage, clipping, nonlinear shrinkage and a factor model.
- **Build.** `firm.covest`: covariance estimators (sample; Ledoit-Wolf linear to identity and constant-correlation targets; analytical nonlinear shrinkage; Marchenko-Pastur clipping; PCA factor model with a diagonal remainder) and an out-of-sample risk evaluator; Python.
- **Weekend problem.** The portfolio that promised 6% — named result: the realised-to-predicted risk ratio of the sample minimum-variance portfolio at q = N/T, against the 1/(1-q) prediction, and the ratio each better estimator achieves.
- **Facts to verify.** Marchenko and Pastur 1967 (Math. USSR Sbornik); Laloux, Cizeau, Bouchaud and Potters 1999 (Physical Review Letters) noise dressing; Plerou et al. 1999 (Physical Review Letters); Ledoit and Wolf 2004 (J. Multivariate Analysis; J. Portfolio Management 'Honey, I shrunk'); Ledoit and Wolf 2020 (Annals of Statistics) analytical nonlinear shrinkage; Baik, Ben Arous and Péché 2005 (Annals of Probability); Johnstone 2001 (Annals of Statistics) spiked model; Fan, Liao and Mincheva 2013 (JRSS B) POET; Bun, Bouchaud and Potters 2017 (Physics Reports); Pearson 1901 / Hotelling 1933 principal components.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | V. A. Marcenko and L. A. Pastur, "Distribution of eigenvalues for some sets of random matrices", Mathematics of the USSR-Sbornik 1(4) (1967), 457-483 | Crossref record | https://doi.org/10.1070/SM1967v001n04ABEH001994 | 2026-09-24 | vol 1(4), pp 457-483 | thm MP; omsources |
| F2 | L. Laloux, P. Cizeau, J.-P. Bouchaud and M. Potters, "Noise dressing of financial correlation matrices", Physical Review Letters 83(7) (1999), 1467-1470 | Crossref record | https://doi.org/10.1103/PhysRevLett.83.1467 | 2026-09-24 | vol 83(7), pp 1467-1470 | section 2 (real correlation matrices inside MP); def clipping; omsources |
| F3 | O. Ledoit and M. Wolf, "A well-conditioned estimator for large-dimensional covariance matrices", J. Multivariate Analysis 88(2) (2004), 365-411 | Crossref record | https://doi.org/10.1016/S0047-259X(03)00096-4 | 2026-09-24 | vol 88(2), pp 365-411 | def linear shrinkage; firm.covest; omsources |
| F4 | O. Ledoit and M. Wolf, "Honey, I shrunk the sample covariance matrix", J. Portfolio Management 30(4) (2004), 110-119 | Crossref record | https://doi.org/10.3905/jpm.2004.110 | 2026-09-24 | vol 30(4), pp 110-119 | constant-correlation target; omsources |
| F5 | O. Ledoit and M. Wolf, "Analytical nonlinear shrinkage of large-dimensional covariance matrices", Annals of Statistics 48(5) (2020) | Crossref record | https://doi.org/10.1214/19-AOS1921 | 2026-09-24 | vol 48(5), 2020 | def nonlinear shrinkage; firm.covest; omsources |
| F6 | I. M. Johnstone, "On the distribution of the largest eigenvalue in principal components analysis", Annals of Statistics 29(2) (2001) | Crossref record | https://doi.org/10.1214/aos/1009210544 | 2026-09-24 | vol 29(2), 2001 | def spiked model; omsources |
| F7 | J. Baik, G. Ben Arous and S. Peche, "Phase transition of the largest eigenvalue for nonnull complex sample covariance matrices", Annals of Probability 33(5) (2005) | Crossref record | https://doi.org/10.1214/009117905000000233 | 2026-09-24 | title says complex sample covariance matrices | section 2 (spike transition); omsources |
| F8 | J. Baik and J. W. Silverstein, "Eigenvalues of large sample covariance matrices of spiked population models", J. Multivariate Analysis 97(6) (2006), 1382-1408 | Crossref record | https://doi.org/10.1016/j.jmva.2005.08.003 | 2026-09-24 | vol 97(6), pp 1382-1408 | section 2 (real case); omsources |
| F9 | J. Fan, Y. Liao and M. Mincheva, "Large covariance estimation by thresholding principal orthogonal complements", JRSS B 75(4) (2013), 603-680 | Crossref record | https://doi.org/10.1111/rssb.12016 | 2026-09-24 | vol 75(4), pp 603-680 | section 4 (POET); omsources |
| F10 | J. Bun, J.-P. Bouchaud and M. Potters, "Cleaning large correlation matrices: tools from random matrix theory", Physics Reports 666 (2017), 1-109 | Crossref record | https://doi.org/10.1016/j.physrep.2016.10.005 | 2026-09-24 | vol 666, pp 1-109 | omsources |

## EXCLUDED

- Plerou et al. 1999, Pearson 1901, Hotelling 1933 (planned): not cited.
- The in-sample (1 - q) / out-of-sample 1/(1 - q) scaling is stated and checked by simulation, not sourced.
- The 200-stock factor truth is a simulation. Brief deviation: hook uses 200 stocks and 500 days (q = 0.4, promised 5.7%, delivered 9.6%) rather than 500 stocks, since q near 1 makes the sample matrix singular.

