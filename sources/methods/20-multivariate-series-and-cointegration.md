# 20. Multivariate Series and Cointegration — brief and source ledger

## Brief

- **Hook.** Two-year, five-year and ten-year Treasury yields each look like random walks, but the butterfly that buys the five-year against the wings does not wander off; the question is which weights make it stationary, and they are not the textbook one-two-one.
- **Sections.** Vector autoregressions; Cointegration and the error-correction form; Rank tests; Causality in the predictive sense.
- **Defines.** vector autoregression, impulse response function, forecast-error variance decomposition, cointegration, cointegrating vector, vector error-correction model, Engle--Granger test, Johansen test, cointegration rank, Granger causality.
- **Uses (defined earlier).** unit root, Dickey--Fuller test, spurious regression, weak stationarity, ordinary least squares, half-life, curve fly, maximum likelihood estimator, information criterion.
- **Results (named theorems, not terms).** stationarity condition of a VAR; Granger representation theorem; Johansen's reduced-rank maximum likelihood and the trace statistic; Engle-Granger critical values differ from Dickey-Fuller's.
- **Tutorial.** Fit a vector error-correction model to daily 2-, 5- and 10-year Treasury yields (FRED), choose the cointegration rank by the Johansen trace test, and compare the estimated butterfly weights and half-life with the one-two-one fly.
- **Build.** `firm.coint`: VAR estimation and impulse responses, Engle-Granger with MacKinnon critical values, Johansen trace and maximum-eigenvalue tests with critical values, VECM fitting, Granger-causality F-tests; Python.
- **Weekend problem.** The fly that mean-reverts — named result: the Johansen butterfly weights of the 2s5s10s fly and its half-life, against those of the one-two-one fly.
- **Facts to verify.** FRED DGS2, DGS5, DGS10 (H.15), public domain; Sims 1980 (Econometrica); Granger 1969 (Econometrica); Engle and Granger 1987 (Econometrica); Johansen 1988 (JEDC) / 1991 (Econometrica); MacKinnon, Haug and Michelis 1999 (J. Applied Econometrics) critical values.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | FRED DGS2, DGS5 and DGS10 (H.15), daily, 1976-06-01 to 2026-09-22 (12,574 common days) | FRED graph CSV download | https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS5 | 2026-09-24 | first 1976-06-01, last 2026-09-22 in the joined file | tutorial, figures, problem; data/methods/ust_2y5y10y_daily_1976_2026.csv |
| F2 | Board of Governors website information is in the public domain unless otherwise indicated; cite the Board | Federal Reserve Board, website disclaimer | https://www.federalreserve.gov/disclaimer.htm | 2026-09-24 | "information on Board's website is in the public domain and may be copied and distributed without permission" | data/methods/LICENSES.md |
| F3 | C. A. Sims, "Macroeconomics and reality", Econometrica 48(1) (1980), from p. 1 | Crossref record | https://doi.org/10.2307/1912017 | 2026-09-24 | vol 48(1), p 1 | def VAR; omsources |
| F4 | C. W. J. Granger, "Investigating causal relations by econometric models and cross-spectral methods", Econometrica 37(3) (1969), from p. 424 | Crossref record | https://doi.org/10.2307/1912791 | 2026-09-24 | vol 37(3), p 424 | def Granger causality; omsources |
| F5 | R. F. Engle and C. W. J. Granger, "Co-integration and error correction: representation, estimation, and testing", Econometrica 55(2) (1987), from p. 251 | Crossref record | https://doi.org/10.2307/1913236 | 2026-09-24 | vol 55(2), p 251 | def EG test; Granger representation; omsources |
| F6 | S. Johansen, "Statistical analysis of cointegration vectors", J. Economic Dynamics and Control 12(2-3) (1988), 231-254; "Estimation and hypothesis testing of cointegration vectors in Gaussian vector autoregressive models", Econometrica 59(6) (1991), from p. 1551 | Crossref records | https://doi.org/10.1016/0165-1889(88)90041-3 | 2026-09-24 | JEDC 12, pp 231-254; Econometrica doi 10.2307/2938278, vol 59(6) | def Johansen test; omsources |
| F7 | J. G. MacKinnon (2010), Working Paper 1227, Table 2, tau_c for N = 3: 1% -4.29374 -14.4354 -33.195 47.433; 5% -3.74066 -8.5631 -10.852 27.982; 10% -3.45218 -6.2143 -3.718; N = 2: 1% -3.89644 -10.9519 -22.527; 5% -3.33613 -6.1101 -6.823; 10% -3.04445 -4.2412 -2.720 | author's PDF | http://qed.econ.queensu.ca/working_papers/papers/qed_wp_1227.pdf | 2026-09-24 | Table 2 rows N = 2 and N = 3, variant tau_c | section 3 (Engle-Granger); firm.coint MACKINNON_C; exercise 3; iq 3 |

## EXCLUDED

- MacKinnon, Haug and Michelis 1999 (planned): not used; the Johansen critical values are simulated by firm.coint.johansen_crit_sim (T = 2000, 20,000 replications, seed 20) and re-simulated in the acceptance tests.
- The one-two-one fly is a convention, not a sourced fact.

