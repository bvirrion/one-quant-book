# 10. Stochastic Volatility — brief and source ledger

## Brief

- **Hook.** Asked why the calibrated correlation of the Heston model is minus 0.7, an index-options trader answers without a formula: because when the index falls, volatility rises.
- **Sections.** Stochastic volatility models; The Heston model; The characteristic function and pricing; Calibration; What the parameters mean to a trader.
- **Defines.** stochastic volatility model, Heston model, volatility of volatility, spot--volatility correlation, mixing formula.
- **Uses (defined earlier).** square-root process, Feller condition (Book 4 ch. 4), characteristic function (Book 4 ch. 1), Fourier inversion (Book 4 ch. 28), complete market (ch. 1), calibration (Book 4 ch. 24), local volatility (ch. 9).
- **Tutorial.** Price with the Heston characteristic function in its stable form, calibrate the five parameters to a synthetic surface, and show how each parameter moves the smile.
- **Build.** `firm.heston`: Heston characteristic function, semi-analytic pricer, calibration (numpy Levenberg-Marquardt), and the path generator used in chapter 23.
- **Weekend problem.** Reading the parameters — named result: the change in the one-year 90-110 skew for a change of 0.2 in correlation, and the volatility of volatility that matches a quoted butterfly.
- **Facts to verify.** Heston 1993 RFS; Albrecher et al. 2007 'The little Heston trap'; Hull-White 1987 JF; Romano-Touzi 1997 mixing; leverage effect evidence (Black 1976; Bouchaud, Matacz, Potters 2001).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Heston, "A closed-form solution for options with stochastic volatility with applications to bond and currency options", RFS 6(2), April 1993, 327-343: closed form for European calls with correlated stochastic volatility | Oxford Academic record | https://academic.oup.com/rfs/article-abstract/6/2/327/1574747 | 2026-09-24 | "a closed-form solution for the price of a European call option on an asset with stochastic volatility" (abstract via search) | def Heston; omsources |
| F2 | Albrecher, Mayer, Schoutens, Tistaert, "The little Heston trap", Wilmott 2007, 83-92 | TU Graz research portal record | https://tugraz.elsevierpure.com/en/publications/the-little-heston-trap/ | 2026-09-24 | bibliographic record (search summary: Wilmott Magazine 2007, pp. 83-92) | prop cf; omsources |
| F3 | Hull and White, JF 42(2) (1987) 281-300: option price in series form when volatility is independent of the stock price | IDEAS/RePEc | https://ideas.repec.org/a/bla/jfinan/v42y1987i2p281-300.html | 2026-09-24 | "The option price is determined in series form for the case in which the stochastic volatility is independent of the stock price" (search summary) | prop mixing; omsources |
| F4 | Romano and Touzi, Mathematical Finance 7(4) (1997) 399-412: stochastic volatility with correlation | EconPapers | https://econpapers.repec.org/RePEc:bla:mathfi:v:7:y:1997:i:4:p:399-412 | 2026-09-24 | "extends recent results in a stochastic volatility model to the case where the asset price and its volatility variations are correlated" (search summary) | prop mixing; omsources |
| F5 | Leverage effect: negative correlation between past returns and future volatility, moderate and decaying over about 50 days for single stocks, much stronger but faster-decaying for indices; PRL 87(22) 228701 (2001) | Bouchaud, Matacz, Potters (arXiv cond-mat/0101120) | https://arxiv.org/abs/cond-mat/0101120 | 2026-09-24 | "For individual stocks, this correlation is moderate and decays exponentially over 50 days, while for stock indices, it is much stronger but decays faster" (abstract via search) | §1; omsources |

## EXCLUDED

- None.
