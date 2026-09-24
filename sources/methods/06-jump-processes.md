# 6. Jump Processes — brief and source ledger

## Brief

- **Hook.** On 19 October 1987 the Dow Jones Industrial Average fell 22.6% in one session; measured in the previous year's daily standard deviations it was a move no diffusion assigns a probability distinguishable from zero, and one a jump process makes merely rare.
- **Sections.** Poisson and compound Poisson processes; Itô's formula with jumps; Lévy processes and the Lévy--Khintchine formula; Cumulants and the term structure of kurtosis.
- **Defines.** Poisson process, compound Poisson process, compensated Poisson process, jump-diffusion, semimartingale, Lévy process, infinitely divisible distribution, Lévy measure, Lévy triplet, characteristic exponent, cumulant, subordinator.
- **Uses (defined earlier).** hazard rate, characteristic function, Brownian motion, martingale, Itô's formula (result), infinitesimal generator, stochastic exponential.
- **Results (named theorems, not terms).** Itô's formula for finite-activity jump-diffusions; Lévy-Khintchine formula; Lévy-Itô decomposition (stated); exponential-martingale condition for exp(X_t); excess kurtosis of a Lévy process decays like 1/t.
- **Tutorial.** Simulate compound Poisson and jump-diffusion paths, recover the first four cumulants and the Lévy-Khintchine characteristic function from the paths, and show the excess kurtosis of increments falling like 1/t across horizons.
- **Build.** `firm.levy`: Lévy toolkit (characteristic exponents of Brownian motion with drift, Merton- and Kou-type jump-diffusions, variance gamma, NIG; cumulants; path simulation by compound Poisson and by subordination); Python.
- **Weekend problem.** Twenty standard deviations — named result: the size of the 19 October 1987 fall in standard deviations of the previous year's daily returns, its diffusion probability, and the jump intensity and mean jump size that make a 20% one-day fall a once-in-fifty-years event, with the daily and monthly excess kurtosis they imply.
- **Facts to verify.** 19 October 1987: DJIA -22.6% (and S&P 500 -20.5%), from a primary source (Fed history / Brady Commission report / SEC); previous-year DJIA daily volatility (from a free dataset or a cited statistic); Lévy 1934 / Khintchine 1937 (Lévy-Khintchine); Merton 1976 (Journal of Financial Economics) jump-diffusion; Kou 2002 (Management Science); Madan, Carr and Chang 1998 variance gamma.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | On 19 October 1987 the Dow Jones Industrial Average "crashed at the opening bell and eventually finished down 508 points, or 22.6 percent" | Federal Reserve History, "Stock Market Crash of 1987" | https://www.federalreservehistory.org/essays/stock-market-crash-of-1987 | 2026-09-24 | "dropped 22.6 percent in a single trading session" | hook; omsources |
| F2 | The S&P 500's 19 October 1987 return was "a whopping 20.98 sigma event", with sigma = 0.98%, the standard deviation of daily returns from 3 January 1950 to 31 July 2012 | CFA Institute Enterprising Investor, "Fact file: S&P 500 sigma events", 27 August 2012 | https://rpc.cfainstitute.org/blogs/enterprising-investor/2012/fact-file-sp-500s-sigma-events | 2026-09-24 | "the largest negative sigma event was the famous 19 October 1987 crash, which was a whopping 20.98 sigma event"; daily sd 0.98% over 1950-2012 | hook; problem |
| F3 | R. C. Merton, "Option pricing when underlying stock returns are discontinuous", Journal of Financial Economics 3 (1976), 125-144 | Scientific Research Publishing reference record; RePEc working paper | https://ideas.repec.org/p/mit/sloanp/1899.html | 2026-09-24 | JFE 3, 125-144 | omsources |
| F4 | S. G. Kou, "A jump-diffusion model for option pricing", Management Science 48(8) (2002), 1086-1101: double-exponential jumps | INFORMS record, doi 10.1287/mnsc.48.8.1086.166 | https://pubsonline.informs.org/doi/10.1287/mnsc.48.8.1086.166 | 2026-09-24 | Management Science 48, 1086-1101 | build (psi_kou); omsources |
| F5 | R. Cont and P. Tankov, Financial Modelling with Jump Processes, Chapman & Hall/CRC, 2004 (Lévy-Khintchine, Lévy-Itô, triplet convention) | Routledge book page | https://www.routledge.com/Financial-Modelling-with-Jump-Processes/Cont-Tankov/p/book/9781584884132 | 2026-09-24 | 1st edition, 2004, ISBN 9781584884132 | thm Lévy-Khintchine (admitted); omsources |

## EXCLUDED

- Lévy 1934 / Khintchine 1937 and Madan-Carr-Chang 1998 (planned): not cited in the text; the variance gamma model itself is One Quant Book 5, chapter 13.
- 'Longer than the age of the universe' for 10^97 days: stated without a number; any cosmological age (about 10^13 days) is 84 orders of magnitude short.
- The jump-diffusion calibration (lambda = 0.5, sigma_J = 5%, 50 years) is the problem's modelling choice, not a fact; its outputs are asserted in test_solutions.py.

