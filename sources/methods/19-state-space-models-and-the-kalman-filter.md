# 19. State-Space Models and the Kalman Filter — brief and source ledger

## Brief

- **Hook.** A desk hedges Brent exposure with WTI futures using a 60-day rolling regression; when the relationship shifts, the rolling hedge ratio takes two months to follow. A filter that treats the ratio itself as a slowly moving hidden state follows in days.
- **Sections.** Linear Gaussian state-space models; The Kalman filter; The smoother and expectation--maximisation; Particle filters; A time-varying hedge ratio.
- **Defines.** state-space model, local level model, Kalman filter, Kalman gain, innovation, prediction-error decomposition, Kalman smoother, expectation--maximisation algorithm, particle filter, sequential importance resampling, signal-to-noise ratio.
- **Uses (defined earlier).** Bayesian update, posterior distribution, maximum likelihood estimator, Markov chain Monte Carlo, effective sample size, ordinary least squares, autoregressive process, Radon--Nikodym derivative.
- **Results (named theorems, not terms).** Kalman filter as Gaussian conditioning (derived); steady-state gain of the local level model as a function of the signal-to-noise ratio; likelihood by the prediction-error decomposition; Rauch-Tung-Striebel smoother; EM increases the likelihood at every step.
- **Tutorial.** Track the hedge ratio of daily Brent price changes on WTI price changes (EIA spot prices via FRED) with a Kalman filter, estimate the two noise variances by maximum likelihood, and compare hedge errors with the 60-day rolling regression; smooth the path.
- **Build.** `firm.kalman`: linear Gaussian Kalman filter and smoother with the prediction-error likelihood, EM for the noise covariances, a bootstrap particle filter, and a streaming hedge-ratio tracker; Python.
- **Weekend problem.** The hedge ratio that moved — named result: the reduction in hedge-error variance of the Kalman hedge ratio against the 60-day rolling regression over the sample, and the estimated signal-to-noise ratio.
- **Facts to verify.** FRED DCOILWTICO and DCOILBRENTEU (EIA spot prices), public domain; WTI spot settled at -36.98 dollars (EIA spot) on 20 April 2020, for handling of the negative price; Kalman 1960 (J. Basic Engineering); Kalman and Bucy 1961; Rauch, Tung and Striebel 1965 (AIAA Journal); Dempster, Laird and Rubin 1977 (JRSS B); Shumway and Stoffer 1982 (J. Time Series Analysis); Gordon, Salmond and Smith 1993 (IEE Proceedings F) bootstrap filter.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | FRED DCOILWTICO and DCOILBRENTEU (EIA spot prices), daily, 2010-01-04 to 2026-09-22; WTI spot -36.98 on 20 Apr 2020 (Brent 17.36); 22 Sep 2026: WTI 96.41, Brent 114.89 | FRED graph CSV download | https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO | 2026-09-24 | rows "2020-04-20,-36.98" (WTI) and "2020-04-20,17.36" (Brent); 4,098 common days | hook, tutorial, figures, problem; data/methods/wti_brent_daily_2010_2026.csv |
| F2 | U.S. government publications (EIA content) are in the public domain | EIA, Copyrights and Reuse | https://www.eia.gov/about/copyrights_reuse.php | 2026-09-24 | "U.S. government publications are in the public domain and are not subject to copyright protection" | data/methods/LICENSES.md |
| F3 | R. E. Kalman, "A new approach to linear filtering and prediction problems", Journal of Basic Engineering 82(1) (1960), 35-45 | Crossref record | https://doi.org/10.1115/1.3662552 | 2026-09-24 | vol 82(1), pp 35-45 | def Kalman filter; omsources |
| F4 | H. E. Rauch, F. Tung and C. T. Striebel, "Maximum likelihood estimates of linear dynamic systems", AIAA Journal 3(8) (1965), 1445-1450 | Crossref record | https://doi.org/10.2514/3.3166 | 2026-09-24 | vol 3(8), pp 1445-1450 | def smoother; omsources |
| F5 | A. P. Dempster, N. M. Laird and D. B. Rubin, "Maximum likelihood from incomplete data via the EM algorithm", JRSS B 39(1) (1977) | Crossref record | https://doi.org/10.1111/j.2517-6161.1977.tb01600.x | 2026-09-24 | vol 39(1), 1977 | def EM; omsources |
| F6 | R. H. Shumway and D. S. Stoffer, "An approach to time series smoothing and forecasting using the EM algorithm", J. Time Series Analysis 3(4) (1982), 253-264 | Crossref record | https://doi.org/10.1111/j.1467-9892.1982.tb00349.x | 2026-09-24 | vol 3(4), pp 253-264 | section 4; omsources |
| F7 | N. J. Gordon, D. J. Salmond and A. F. M. Smith, "Novel approach to nonlinear/non-Gaussian Bayesian state estimation", IEE Proceedings F 140(2) (1993), from p. 107 | Crossref record | https://doi.org/10.1049/ip-f-2.1993.0015 | 2026-09-24 | vol 140(2), p 107 | def SIR; omsources |
| F8 | ECB euro reference rate, USD per EUR (series EXR.D.USD.EUR.SP00.A), last 1,000 fixings to 23 Sep 2026; +2.7% on 3 Apr 2025 | ECB Data Portal API (csvdata) | https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?format=csvdata | 2026-09-24 | data/methods/eur_fx_ecb_1999_2026.csv | section 5 (stochastic volatility), figure |
| F9 | EIA Today in Energy (id 46336): WTI traded at negative prices on April 20 [2020], the first time the WTI futures price fell below zero since trading began in 1983; between March 13 and May 1 commercial crude inventories at Cushing, Oklahoma rose by 27 million barrels to 83% of working storage capacity, contributing to the negative price | EIA | https://www.eia.gov/todayinenergy/detail.php?id=46336 | 2026-09-24 | quoted sentences on Cushing (27 million barrels, 83%) and "first time ... since trading began in 1983" | section 2; omsources |
| F10 | ECB Financial Stability Review, November 2025, special feature "What safe haven after the April US tariff announcement?": the US tariff announcement of 2 April 2025 triggered a risk-off episode in which the US dollar depreciated strongly while Treasury yields rose, the opposite of the usual pattern | ECB | https://www.ecb.europa.eu/press/financial-stability-publications/fsr/special/html/ecb.fsrart202511_01~fdf147a04a.en.html | 2026-09-24 | "2 April risk-off is the US tariff announcement on 2 April 2025"; "the US dollar depreciated strongly while US Treasury yields rose" | section 5; omsources |

## EXCLUDED

- Kalman and Bucy 1961 (planned): not cited.
- Brief deviation (hook): the brief expected the filter to follow shifts in days; with maximum likelihood on 2010-2026 data it is as slow as the 60-day window (half-response 30 days) and hedges 0.7% better. The text reports that finding and the speed-noise trade-off instead.
- The April 2020 negative WTI price and the 3 Apr 2025 EUR/USD move: context restored in Phase C (last two F rows).

