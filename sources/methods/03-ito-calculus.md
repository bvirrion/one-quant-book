# 3. Itô Calculus — brief and source ledger

## Brief

- **Hook.** A junior's backtest of a mean-reversion rule shows a Sharpe ratio of 4; the rule reads the closing price and trades at that same close. Shift the position by one bar and the Sharpe ratio falls to 0.3: the first backtest was not an Itô integral.
- **Sections.** The Itô integral; Itô's formula in one and several dimensions; Local martingales and the stochastic exponential; The representation theorem.
- **Defines.** simple process, Itô integral, Itô process, quadratic covariation, Stratonovich integral, local martingale, stochastic exponential.
- **Uses (defined earlier).** Brownian motion, quadratic variation, martingale, adapted process, filtration, volatility decay, leveraged ETF, P\&L attribution.
- **Results (named theorems, not terms).** Itô isometry; Itô's formula (one and several dimensions, product rule); Lévy's characterisation of Brownian motion; martingale representation theorem; a strict local martingale (inverse three-dimensional Bessel process, stated).
- **Tutorial.** Compute the integral of W against itself with left-point and midpoint sums and recover the t/2 gap; verify Itô's formula on the logarithm of a geometric path; then run a same-bar and a next-bar backtest of one rule and measure the covariation term that separates them.
- **Build.** `firm.stochint`: discrete stochastic integrals with enforced adaptedness (position fixed at t_i earns the increment to t_{i+1}), realised quadratic variation and covariation accumulators, and a look-ahead detector that flags a strategy whose P&L carries a covariation term; Python.
- **Weekend problem.** The look-ahead in the backtest — a position that reads the bar it trades on; named result: the spurious Sharpe ratio produced by the covariation term of a same-bar mean-reversion rule on a pure random walk, and its exact expression.
- **Facts to verify.** Itô 1944 (Proc. Imperial Academy, Tokyo) stochastic integral; Itô 1951 formula; Stratonovich 1966; Doléans-Dade 1970 stochastic exponential; Lévy characterisation (Lévy 1948).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | K. Itô, "Stochastic integral", Proceedings of the Imperial Academy (Tokyo) 20(8), 1944, 519-524 | Project Euclid record, doi 10.3792/pia/1195572786 | https://projecteuclid.org/journals/proceedings-of-the-imperial-academy/volume-20/issue-8/Stochastic-integral/10.3792/pia/1195572786.full | 2026-09-24 | volume 20, issue 8, pp. 519-524 | omsources |
| F2 | K. Itô, "On a formula concerning stochastic differentials", Nagoya Mathematical Journal 3 (1951), 55-65: Itô's formula | Project Euclid record | https://projecteuclid.org/euclid.nmj/1118799221 | 2026-09-24 | Nagoya Math. J. 3 (1951) 55-65 | thm Itô's formula; omsources |
| F3 | R. L. Stratonovich, "A new representation for stochastic integrals and equations", SIAM Journal on Control 4 (1966), 362-371 (Russian original 1964) | search summary of citing literature (arXiv 1406.0112 and others) | https://arxiv.org/pdf/1406.0112 | 2026-09-24 | "SIAM Journal on Control, volume 4, pages 362-371, 1966" | def Stratonovich; omsources |
| F4 | I. Karatzas and S. E. Shreve, Brownian Motion and Stochastic Calculus, Springer, 2nd ed. 1991 (GTM 113): proofs of Itô's formula (§3.3), Lévy's characterisation and martingale representation (§3.3-3.4) | Google Books record (as in ch. 2 F6) | https://books.google.com/books/about/Brownian_Motion_and_Stochastic_Calculus.html?id=ATNy_Zg3PSsC | 2026-09-24 | 2nd edition, 1991, eBook ISBN 978-1-4612-0949-2 | partial proof; admitted theorems; omsources |

## EXCLUDED

- Doléans-Dade 1970 and Lévy 1948 (planned facts): named in no sentence of the text; not cited.
- The look-ahead Sharpe ratio, the Itô sums and the GBM mean/median are derived and simulated in the chapter (test_solutions.py).

