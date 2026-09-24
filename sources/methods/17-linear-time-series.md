# 17. Linear Time Series — brief and source ledger

## Brief

- **Hook.** The spread between two-year and ten-year Treasury yields has a daily autocorrelation of 0.998. A regression of tomorrow's spread on today's gives a slope 'significantly' below one; under a unit root the usual t-table is the wrong one.
- **Sections.** Stationarity and autocorrelation; Autoregressive and moving-average models; The spectral view; Unit roots; Long memory.
- **Defines.** stationary process, weak stationarity, autocovariance function, autocorrelation function, partial autocorrelation function, white noise, autoregressive process, moving-average process, ARMA process, information criterion, spectral density, periodogram, unit root, spurious regression, Dickey--Fuller test, long memory, fractional differencing, Hurst exponent, fractional Brownian motion.
- **Uses (defined earlier).** Ornstein--Uhlenbeck process, half-life, mean reversion, ordinary least squares, HAC estimator, Brownian motion, maximum likelihood estimator, curve fly, steepener.
- **Results (named theorems, not terms).** Wold decomposition theorem; stationarity and invertibility conditions of ARMA; Dickey-Fuller distribution as a functional of Brownian motion; Kendall's small-sample bias of the AR(1) coefficient; autocorrelations of a long-memory process decay like a power law.
- **Tutorial.** Fit autoregressions to the daily 2s10s Treasury spread (FRED), run the augmented Dickey-Fuller test, and correct the half-life estimate for the small-sample bias of the AR(1) coefficient.
- **Build.** `firm.tsa`: time-series toolkit (ACF and PACF with bands, Yule-Walker and conditional maximum likelihood for ARMA, augmented Dickey-Fuller with MacKinnon critical values, periodogram, fractional differencing, rescaled-range and log-periodogram Hurst estimates); Python.
- **Weekend problem.** The half-life of a spread — named result: the half-life of mean reversion of the 2s10s spread implied by an AR(1), its bias-corrected value, and whether a unit root can be rejected.
- **Facts to verify.** FRED series DGS2 and DGS10 (Board of Governors, H.15), public domain; Box and Jenkins 1970; Wold 1938; Dickey and Fuller 1979 (JASA); Said and Dickey 1984; MacKinnon 1996 / 2010 response-surface critical values; Kwiatkowski, Phillips, Schmidt and Shin 1992 (J. Econometrics); Granger and Newbold 1974 (J. Econometrics) spurious regression; Kendall 1954 bias; Hurst 1951; Mandelbrot and Van Ness 1968 (SIAM Review); Granger and Joyeux 1980; Hosking 1981; Geweke and Porter-Hudak 1983.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | FRED DGS2 and DGS10, daily Treasury constant-maturity yields (H.15), 1 Jun 1976 to 22 Sep 2026; 22 Sep 2026: 4.71 and 4.96 | FRED graph CSV download | https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10 | 2026-09-24 | 12,574 common days; first 1976-06-01, last 2026-09-22 | tutorial, figures, problem; data/methods/ust_2y10y_daily_1976_2026.csv |
| F2 | Board of Governors website information is in the public domain unless otherwise indicated; cite the Board | Federal Reserve Board, website disclaimer | https://www.federalreserve.gov/disclaimer.htm | 2026-09-24 | "information on Board's website is in the public domain and may be copied and distributed without permission. Please cite to the Board" | data/methods/LICENSES.md |
| F3 | J. G. MacKinnon, "Critical values for cointegration tests", Queen's Economics Department Working Paper 1227 (2010), Table 2: tau_nc and tau_c response surfaces (N = 1); Table 3: tau_ct; e.g. tau_c 5%: -2.86154, -2.8903, -4.234, -40.040 | author's PDF | http://qed.econ.queensu.ca/working_papers/papers/qed_wp_1227.pdf | 2026-09-24 | Table 2 row "1 tau_c 5% 15,000 -2.86154 (0.000068) -2.8903 -4.234 -40.040"; critical value = b_inf + b1/T + b2/T^2 + b3/T^3 | section 4; firm.tsa MACKINNON; exercise 6; omsources |
| F4 | D. A. Dickey and W. A. Fuller, "Distribution of the estimators for autoregressive time series with a unit root", JASA 74(366a) (1979), 427-431 | Crossref record | https://doi.org/10.1080/01621459.1979.10482531 | 2026-09-24 | vol 74, pp 427-431 | def Dickey-Fuller; omsources |
| F5 | S. E. Said and D. A. Dickey, "Testing for unit roots in autoregressive-moving average models of unknown order", Biometrika 71(3) (1984), 599-607 | Crossref record | https://doi.org/10.1093/biomet/71.3.599 | 2026-09-24 | vol 71(3), pp 599-607 | def augmented DF; omsources |
| F6 | C. W. J. Granger and P. Newbold, "Spurious regressions in econometrics", Journal of Econometrics 2(2) (1974), 111-120 | Crossref record | https://doi.org/10.1016/0304-4076(74)90034-7 | 2026-09-24 | vol 2(2), pp 111-120 | section 4; omsources |
| F7 | M. G. Kendall, "Note on bias in the estimation of autocorrelation", Biometrika 41(3-4) (1954), 403-404 | Crossref record | https://doi.org/10.1093/biomet/41.3-4.403 | 2026-09-24 | vol 41, pp 403-404 | prop Kendall bias; omsources |
| F8 | H. E. Hurst, "Long-term storage capacity of reservoirs", Trans. American Society of Civil Engineers 116 (1951), 770-799 | Crossref record | https://doi.org/10.1061/TACEAT.0006518 | 2026-09-24 | vol 116, pp 770-799 | def Hurst exponent; omsources |
| F9 | B. B. Mandelbrot and J. W. Van Ness, "Fractional Brownian motions, fractional noises and applications", SIAM Review 10(4) (1968), 422-437 | Crossref record | https://doi.org/10.1137/1010093 | 2026-09-24 | vol 10(4), pp 422-437 | def fBM; omsources |
| F10 | C. W. J. Granger and R. Joyeux, "An introduction to long-memory time series models and fractional differencing", J. Time Series Analysis 1(1) (1980), 15-29; J. R. M. Hosking, "Fractional differencing", Biometrika 68(1) (1981), 165-176 | Crossref records | https://doi.org/10.1093/biomet/68.1.165 | 2026-09-24 | Hosking vol 68(1) pp 165-176; Granger-Joyeux doi 10.1111/j.1467-9892.1980.tb00297.x vol 1(1) pp 15-29 | def fractional differencing; omsources |
| F11 | J. Geweke and S. Porter-Hudak, "The estimation and application of long memory time series models", J. Time Series Analysis 4(4) (1983), 221-238 | Crossref record | https://doi.org/10.1111/j.1467-9892.1983.tb00371.x | 2026-09-24 | vol 4(4), pp 221-238 | section 5 (log-periodogram); omsources |
| F12 | H. Wold, A Study in the Analysis of Stationary Time Series, Almqvist and Wiksell, 1938 (second edition 1954) | Wikipedia (Herman Wold; Wold's theorem) bibliographies | https://en.wikipedia.org/wiki/Herman_Wold | 2026-09-24 | "1938. A Study in the Analysis of Stationary Time Series, Almqvist & Wiksell" | section 1 (Wold decomposition); omsources |

## EXCLUDED

- Box and Jenkins 1970, KPSS 1992 (planned): not cited in the text (KPSS only named in the Build Stretch field).
- The Dickey-Fuller functional of Brownian motion and the GPH standard error pi/sqrt(24 m) are mathematics, not sourced facts.
- Brief deviation: hook autocorrelation 0.9987 (full sample 1976-2026), not the brief's 0.998.

