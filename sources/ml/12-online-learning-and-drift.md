# 12. Online Learning and Drift — brief and source ledger

## Brief

- **Hook.** A short-horizon model retrained every Sunday loses money every Thursday and Friday of the week after a venue changes its fee schedule; a model that updated itself every hour would have noticed on Monday afternoon.
- **Sections.** Kinds of drift; Recursive estimators and forgetting; Detecting drift; Retraining schedules.
- **Defines.** online learning, recursive least squares, forgetting factor, concept drift, covariate shift, drift detector, Page--Hinkley test, adaptive windowing, retraining schedule.
- **Uses (defined earlier).** Kalman filter (B4.19), state-space model (B4.19), EWMA volatility (B4.18), CUSUM test (B7.13), structural break (B7.13), signal half-life (B7.13), sequential test (B7.21), stochastic gradient descent (B4.24), ridge regression (B4.16), walk-forward analysis (B7.20), prediction target (B7.6), forecast horizon (B7.6), information coefficient (B7.6), in-sample (B7.20), out-of-sample (B7.20), cross-validation (B4.16).
- **Tutorial.** On firm.tape sessions (and Book 10's simulator once frozen) whose informed-flow share and fee regime change at scheduled times, compare a static model, weekly and daily batch retraining, recursive least squares with several forgetting factors and online SGD; run Page-Hinkley, ADWIN and CUSUM detectors on the model's errors and measure detection delay against false alarms. Data: synthetic.
- **Build.** `firm.onlinelearn`: recursive least squares with forgetting (equivalence to a Kalman filter with a random-walk state), online SGD, Page-Hinkley and ADWIN detectors with calibrated thresholds, and a retraining scheduler that combines calendar and detector triggers; Python.
- **Weekend problem.** The half-life of a model -- named result: the forgetting factor that minimises out-of-sample loss as a function of the regime's mean duration, and each detector's delay at one false alarm a month.
- **Facts to verify.** Haykin 2002 Adaptive Filter Theory (RLS); Page 1954 continuous inspection schemes (Biometrika); Bifet and Gavalda 2007 learning from time-changing data with adaptive windowing (SDM); Gama et al. 2014 a survey on concept drift adaptation (ACM Computing Surveys); Widmer and Kubat 1996 learning in the presence of concept drift and hidden contexts (Machine Learning).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | E. S. Page, "Continuous inspection schemes", Biometrika 41(1/2) 1954 (the cumulative-sum scheme behind the Page--Hinkley test) | Crossref/OpenAlex record | https://doi.org/10.1093/biomet/41.1-2.100 | 2026-09-25 | title, journal and year as registered | def. Page--Hinkley test; omsources |
| F2 | D. V. Hinkley, "Inference about the change-point from cumulative sum tests", Biometrika 58(3) 1971 | Crossref/OpenAlex record | https://doi.org/10.1093/biomet/58.3.509 | 2026-09-25 | title, journal, year; abstract: change point in the mean estimated from a cumulative-sum scheme | def. Page--Hinkley test; omsources |
| F3 | A. Bifet, R. Gavaldà, "Learning from time-changing data with adaptive windowing", SIAM SDM 2007 (ADWIN: window size recomputed online from the rate of change) | Crossref/OpenAlex record | https://doi.org/10.1137/1.9781611972771.42 | 2026-09-25 | abstract: sliding windows whose size is recomputed online according to the rate of change observed in the window | def. adaptive windowing; omsources |
| F4 | J. Gama, I. Žliobaitė, A. Bifet, M. Pechenizkiy et al., "A survey on concept drift adaptation", ACM Computing Surveys 46(4) 2014 (concept drift as a change in the relation between inputs and target) | Crossref/OpenAlex record | https://doi.org/10.1145/2523813 | 2026-09-25 | abstract: concept drift refers to a change over time of the relation between input data and target variable | def. concept drift; omsources |
| F5 | G. Widmer, M. Kubat, "Learning in the presence of concept drift and hidden contexts", Machine Learning 23 1996 | Crossref/OpenAlex record | https://doi.org/10.1007/BF00116900 | 2026-09-25 | title, journal and year as registered | omsources |
| F6 | A. H. Sayed, T. Kailath, "A state-space approach to adaptive RLS filtering", IEEE Signal Processing Magazine 11(3) 1994 (RLS as a Kalman filter for a state-space model) | Crossref/OpenAlex record | https://doi.org/10.1109/79.295229 | 2026-09-25 | title, journal, year; the paper's state-space derivation of RLS | prop. forgetting is a random-walk Kalman filter; omsources |

## EXCLUDED

- Every R-squared, threshold, delay and false-alarm count is computed on firm.onlinelearn.drift_stream (synthetic, planted regime changes) and tested in code/ml/12-online-learning-and-drift/tests/test_solutions.py. The opening fee-schedule example is an illustration, not a reported event.
- Haykin, Adaptive Filter Theory (planned for RLS): no registry record found for the edition; replaced by Sayed and Kailath (1994).
- The brief's firm.tape tutorial (fee regimes on simulated sessions): replaced by a synthetic regression stream so that the truth and the regime times are known exactly.
