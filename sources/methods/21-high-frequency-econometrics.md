# 21. High-Frequency Econometrics — brief and source ledger

## Brief

- **Hook.** Measured from one-second changes in the mid price, a stock's annualised volatility is 60%; from five-minute changes it is 25%. The difference is not the market's; it is the bid--ask bounce and the ticks of the price grid.
- **Sections.** Microstructure noise and the signature plot; Estimators robust to noise; Asynchronous observation and the Epps effect; Jumps at high frequency.
- **Defines.** microstructure noise, bid--ask bounce, Roll's estimator, signature plot, two-scales realised variance, realised kernel, pre-averaging estimator, Epps effect, non-synchronous trading, Hayashi--Yoshida estimator, refresh-time sampling, bipower variation.
- **Uses (defined earlier).** realised variance, integrated variance, realised volatility, quadratic variation, quadratic covariation, mid price, bid--ask spread, Poisson process, jump-diffusion.
- **Results (named theorems, not terms).** bias of realised variance under iid noise grows like 2n times the noise variance; optimal sampling frequency under noise (Bandi-Russell); consistency of two-scales realised variance at rate n^{-1/6}; Hayashi-Yoshida is unbiased for the covariation under asynchronous observation; bipower variation estimates the continuous part of quadratic variation.
- **Tutorial.** Simulate an efficient price with noise, a price grid and Poisson observation times; draw the signature plot; compute realised variance, two-scales and realised-kernel estimates; draw the Epps curve of realised correlation against sampling interval and correct it with Hayashi-Yoshida.
- **Build.** `firm.hfvol`: high-frequency estimators (realised variance at any frequency, subsampled and two-scales, Parzen realised kernel, pre-averaging, bipower variation, Hayashi-Yoshida covariance, refresh-time synchronisation); Python.
- **Weekend problem.** The volatility that depended on the clock — named result: the optimal sampling interval for a given noise-to-signal ratio, and the bias of one-second realised variance that it avoids.
- **Facts to verify.** Roll 1984 (Journal of Finance); Epps 1979 (JASA); Zhang, Mykland and Aït-Sahalia 2005 (JASA); Barndorff-Nielsen, Hansen, Lunde and Shephard 2008 (Econometrica) realised kernels; Jacod, Li, Mykland, Podolskij and Vetter 2009 pre-averaging; Hayashi and Yoshida 2005 (Bernoulli); Bandi and Russell 2008 (Review of Economic Studies); Andersen, Bollerslev, Diebold and Labys 2000 signature plot; Barndorff-Nielsen and Shephard 2004 bipower variation.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | R. Roll, "A simple implicit measure of the effective bid-ask spread in an efficient market", Journal of Finance 39(4) (1984), 1127-1139 | Crossref record | https://doi.org/10.1111/j.1540-6261.1984.tb03897.x | 2026-09-24 | vol 39(4), pp 1127-1139 | def Roll's estimator; omsources |
| F2 | T. W. Epps, "Comovements in stock prices in the very short run", JASA 74(366a) (1979), 291-298 | Crossref record | https://doi.org/10.1080/01621459.1979.10482508 | 2026-09-24 | vol 74, pp 291-298 | def Epps effect; omsources |
| F3 | L. Zhang, P. A. Mykland and Y. Ait-Sahalia, "A tale of two time scales", JASA 100(472) (2005), 1394-1411 | Crossref record | https://doi.org/10.1198/016214505000000169 | 2026-09-24 | vol 100(472), pp 1394-1411 | def TSRV; omsources |
| F4 | O. E. Barndorff-Nielsen, P. R. Hansen, A. Lunde and N. Shephard, "Designing realized kernels to measure the ex post variation of equity prices in the presence of noise", Econometrica 76(6) (2008), 1481-1536 | Crossref record (journal); authors from the SSRN working-paper record doi 10.2139/ssrn.620203 | https://doi.org/10.3982/ECTA6495 | 2026-09-24 | vol 76(6), pp 1481-1536; SSRN record lists Barndorff-Nielsen, Hansen, Lunde, Shephard | def realised kernel; omsources |
| F5 | J. Jacod, Y. Li, P. A. Mykland, M. Podolskij and M. Vetter, "Microstructure noise in the continuous case: the pre-averaging approach", Stochastic Processes and their Applications 119(7) (2009), 2249-2276 | Crossref record (five authors) | https://doi.org/10.1016/j.spa.2008.11.004 | 2026-09-24 | vol 119(7), pp 2249-2276 | def pre-averaging; omsources |
| F6 | T. Hayashi and N. Yoshida, "On covariance estimation of non-synchronously observed diffusion processes", Bernoulli 11(2) (2005) | Crossref record | https://doi.org/10.3150/bj/1116340299 | 2026-09-24 | vol 11(2), 2005 | def HY estimator; omsources |
| F7 | F. M. Bandi and J. R. Russell, "Microstructure noise, realized variance, and optimal sampling", Review of Economic Studies 75(2) (2008), 339-369 | Crossref record | https://doi.org/10.1111/j.1467-937X.2008.00474.x | 2026-09-24 | vol 75(2), pp 339-369 | prop optimal sampling; omsources |
| F8 | O. E. Barndorff-Nielsen and N. Shephard, "Power and bipower variation with stochastic volatility and jumps", Journal of Financial Econometrics 2(1) (2004), 1-37 | Crossref record (lists the first author); co-author from Wikipedia (Realized variance) citation | https://doi.org/10.1093/jjfinec/nbh001 | 2026-09-24 | vol 2(1), pp 1-37; "Bipower variation, introduced by Barndorff-Nielsen and Shephard (2004)" | def bipower variation; omsources |
| F9 | T. G. Andersen, T. Bollerslev, F. X. Diebold and P. Labys, "Great realizations", Risk, March 2000, 105-108: plot of realised volatility against sampling frequency, "which we call the volatility signature plot"; first used in realised-volatility estimation there (Federal Reserve IFDP 905r) | the article (Bollerslev's published-papers PDF) and Board of Governors IFDP 905r | https://public.econ.duke.edu/~boller/Published_Papers/risk_00.pdf | 2026-09-24 | article p. 106: "against sampling frequency, which we call the volatility signature plot"; IFDP 905r (https://www.federalreserve.gov/pubs/ifdp/2007/905/revision/ifdp905r.htm): "appear to have been first used in the context of realized volatility estimation by Andersen, Bollerslev, Diebold, and Labys (2000, p. 106)" | def signature plot; omsources |

## EXCLUDED

- (Restored in Phase C: the Andersen-Bollerslev-Diebold-Labys 2000 attribution of the signature plot is now row F9.)
- The market is simulated (no tick data licence in hand); all numbers are from the simulation. Brief deviation: the hook uses trade prices (the bounce needs trades), with mid quotes shown alongside.

