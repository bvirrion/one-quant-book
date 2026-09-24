# 13. Jumps and Lévy Models — brief and source ledger

## Brief

- **Hook.** A one-week option on a biotechnology share that reports trial results on Thursday: a diffusion needs 150% volatility to price it, a jump model one number, the size of the move.
- **Sections.** Why diffusions fail at short expiries; Jump-diffusions: Merton, Kou, Bates; Pure-jump Lévy models; What cannot be hedged; When jumps matter.
- **Defines.** Merton jump-diffusion model, Kou model, Bates model, variance gamma model.
- **Uses (defined earlier).** Poisson process, compound Poisson process, Lévy process, Lévy--Khintchine formula, subordinator (Book 4 ch. 6), characteristic function (Book 4 ch. 1), complete market (ch. 1), event variance (ch. 8), Heston model (ch. 10).
- **Tutorial.** Price under Merton and variance gamma through their characteristic functions, fit both to a short-dated smile, and compare their short-expiry skew with Heston's.
- **Build.** `firm.jumps`: characteristic functions of Merton, Kou, Bates and variance gamma behind one interface consumed by the transform engine of chapter 24.
- **Weekend problem.** The binary event — named result: the jump size and probability implied by a one-week smile around a scheduled announcement, and the error of the delta hedge across it.
- **Facts to verify.** Merton 1976 JFE; Kou 2002 Management Science; Bates 1996 RFS; Madan, Carr, Chang 1998 variance gamma; Carr, Geman, Madan, Yor 2002 CGMY; Carr-Wu 2003 JF 'What type of process underlies options?'.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Merton, "Option pricing when underlying stock returns are discontinuous", Journal of Financial Economics 3(1-2) (1976) 125-144 | Crossref record 10.1016/0304-405X(76)90022-2 | https://api.crossref.org/works/10.1016/0304-405X(76)90022-2 | 2026-09-24 | Crossref metadata | sec. jump-diffusions, omsources |
| F2 | Kou, "A jump-diffusion model for option pricing", Management Science 48(8) (2002) 1086-1101: a double exponential jump-diffusion, motivated by leptokurtic returns with asymmetric heavy tails and the volatility smile; analytical solutions for calls, puts, interest-rate derivatives and path-dependent options | Crossref record with abstract, 10.1287/mnsc.48.8.1086.166 | https://api.crossref.org/works/10.1287/mnsc.48.8.1086.166 | 2026-09-24 | abstract in Crossref | sec. jump-diffusions, omsources |
| F3 | Bates, "Jumps and stochastic volatility: exchange rate processes implicit in Deutsche mark options", Review of Financial Studies 9(1) (1996) 69-107 | Crossref record 10.1093/rfs/9.1.69 | https://api.crossref.org/works/10.1093/rfs/9.1.69 | 2026-09-24 | Crossref metadata | sec. jump-diffusions, omsources |
| F4 | Madan, Carr, Chang, "The variance gamma process and option pricing", Review of Finance 2(1) (1998) 79-105: Brownian motion with drift evaluated at a gamma time; two extra parameters (drift, volatility of the time change) control skewness and kurtosis; closed forms for density and European options; on S&P 500 data the statistical density is symmetric with some kurtosis and the risk-neutral density negatively skewed with larger kurtosis | Crossref record with abstract, 10.1023/A:1009703431535 | https://api.crossref.org/works/10.1023/A:1009703431535 | 2026-09-24 | abstract in Crossref | sec. pure-jump Levy models, omsources |
| F5 | Carr, Geman, Madan, Yor, "The fine structure of asset returns: an empirical investigation", Journal of Business 75(2) (2002) 305-333 (CGMY) | Crossref record 10.1086/338705 | https://api.crossref.org/works/10.1086/338705 | 2026-09-24 | Crossref metadata | sec. pure-jump Levy models, omsources |
| F6 | Carr and Wu, "What type of process underlies options? A simple robust test", Journal of Finance 58(6) (2003) 2581-2610: at-the-money and out-of-the-money option prices converge to zero at speeds that depend on whether the process is continuous, purely discontinuous or both; S&P 500 options show both a continuous and a jump component | Crossref record with abstract, 10.1046/j.1540-6261.2003.00616.x | https://api.crossref.org/works/10.1046/j.1540-6261.2003.00616.x | 2026-09-24 | abstract in Crossref | sec. why diffusions fail, omsources |

## EXCLUDED

- Merton's (1976) assumption that jump risk is diversifiable and hence unpriced: not re-read (publisher PDF not fetched); the chapter does not state it.
- Typical calibrated jump parameters for index options from the literature: none quoted; every parameter in the chapter is fitted to chapter 9's synthetic surface or is illustrative.
