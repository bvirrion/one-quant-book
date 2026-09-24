# 5. Girsanov and Changes of Numeraire — brief and source ledger

## Brief

- **Hook.** A risk system prices a caplet by simulating the short rate and discounting with a million paths; a colleague switches to the measure attached to the payment-date bond and writes the price in one line. They agree to four decimals, and the second one runs in a microsecond.
- **Sections.** Girsanov's theorem; Numeraires and their martingale measures; The forward measure; The annuity measure; Measure change as a computational tool.
- **Defines.** Novikov's condition, numeraire, money-market account, equivalent martingale measure, risk-neutral measure, change of numeraire, forward measure, annuity measure.
- **Uses (defined earlier).** Radon--Nikodym derivative, density process, change of measure, stochastic exponential, Itô's formula (result), geometric Brownian motion, Ornstein--Uhlenbeck process, caplet, swaption, annuity, par swap rate, zero-coupon rate, Bachelier model.
- **Results (named theorems, not terms).** Girsanov's theorem (Cameron-Martin as the deterministic case); change-of-numeraire theorem (Geman, El Karoui and Rochet); forward prices are forward-measure martingales; swap rates are annuity-measure martingales; Margrabe's exchange-option formula as a worked example.
- **Tutorial.** Price a zero-coupon bond option under an Ornstein-Uhlenbeck short rate three ways: Monte Carlo under the risk-neutral measure with money-market discounting, Monte Carlo under the forward measure, and the closed form the forward measure yields; compare standard errors at equal cost.
- **Build.** `firm.numeraire`: reweighting of simulated paths between numeraires (the density dQ^{N'}/dQ^{N} = (N'_T / N'_0) / (N_T / N_0)), and a martingale test of deflated prices that later pricing libraries run as an acceptance test; Python.
- **Weekend problem.** Two measures, one price — named result: the ratio of Monte Carlo standard errors between risk-neutral and forward-measure pricing of a five-year caplet in the Ornstein-Uhlenbeck short-rate model, i.e. how many risk-neutral paths one forward-measure path is worth.
- **Facts to verify.** Girsanov 1960 (Theory of Probability and its Applications); Cameron and Martin 1944 (Annals of Mathematics); Novikov 1972; Geman, El Karoui and Rochet 1995 (Journal of Applied Probability) changes of numeraire; Margrabe 1978 (Journal of Finance); Jamshidian 1989 (Journal of Finance) forward-measure bond option.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | I. V. Girsanov, "On transforming a certain class of stochastic processes by absolutely continuous substitution of measures", Theory of Probability and its Applications 5 (1960), 285-301 (Russian original: Teor. Veroyatnost. i Primenen. 5:3, 314-330) | Math-Net.Ru record | https://www.mathnet.ru/eng/tvp4837 | 2026-09-24 | "Teor. Veroyatnost. i Primenen., 5:3 (1960), 314-330" | thm Girsanov; omsources |
| F2 | R. H. Cameron and W. T. Martin, "Transformations of Wiener integrals under translations", Annals of Mathematics 45(2) (1944), 386-396 | search summary (Cameron-Martin theorem records) | https://en.wikipedia.org/wiki/Cameron%E2%80%93Martin_theorem | 2026-09-24 | "The Annals of Mathematics, 45 (2): 386-396" | §1 (Cameron-Martin); omsources |
| F3 | A. A. Novikov, "On an identity for stochastic integrals", Theory of Probability and its Applications 17(4) (1972/73), 717-720: Novikov's condition | Math-Net.Ru record | http://www.mathnet.ru/eng/tvp4352 | 2026-09-24 | "Theory Probab. Appl., 17:4 (1973), 717-720" | def Novikov's condition |
| F4 | H. Geman, N. El Karoui and J.-C. Rochet, "Changes of numéraire, changes of probability measure and option pricing", Journal of Applied Probability 32 (1995), 443-458 | Cambridge Core PDF | https://www.cambridge.org/core/services/aop-cambridge-core/content/view/EA730D6C18D56426D491B6A25563C0B3/S002190020010289Xa.pdf/changes_of_numeraire_changes_of_probability_measure_and_option_pricing.pdf | 2026-09-24 | J. Appl. Prob. 32, 443-458 (1995) | thm change of numeraire; omsources |
| F5 | F. Jamshidian, "An exact bond option formula", Journal of Finance 44 (1989), 205-209: closed-form options on zero-coupon bonds under a mean-reverting Gaussian short rate | Wiley Online Library record | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1989.tb02413.x | 2026-09-24 | J. Finance 44: 205-209 | §4 (caplet closed form); omsources |
| F6 | W. Margrabe, "The value of an option to exchange one asset for another", Journal of Finance 33(1) (1978), 177-186 | RePEc/IDEAS record | https://ideas.repec.org/a/bla/jfinan/v33y1978i1p177-86.html | 2026-09-24 | J. Finance 33(1), 177-186 | exercise 6; omsources |

## EXCLUDED

- All numbers (caplet 3.26 bp, forward-measure moments, standard errors, reweighting) are computed in the chapter's code and asserted in test_solutions.py; the OU bond formula is derived in chapter 4.

