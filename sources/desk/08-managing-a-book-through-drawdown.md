# 8. Managing a Book through Drawdown — brief and source ledger

## Brief

- **Hook.** Two portfolio managers are both down eight per cent in March. One strategy has had a bad month; the other's edge died a year ago. Their P&L paths look alike for months, and the head of desk must decide now which one to cut.
- **Sections.** What a drawdown says about a Sharpe ratio; Stop rules and de-risking ladders; Bad luck or broken: sequential evidence; Restart, re-underwrite, retire.
- **Defines.** stop-loss rule, de-risking ladder, time stop, restart rule.
- **Uses (defined earlier).** drawdown (B2.29), maximum drawdown (B7.22), drawdown limit (B8.28), Sharpe ratio (B4.11), drawdown duration (B7.22), CUSUM test (B7.13), sequential test (B7.21), kill criterion (B7.1), strategy lifecycle (B11.28), capture decay (B11.28), risk of ruin (B2.29), fractional Kelly (B2.29), pod (B8.28), limit breach (ch7).
- **Tutorial.** For a strategy whose Sharpe ratio may have fallen from 1 to 0 at an unknown date, compute from its daily P&L the posterior probability that it has broken (a two-state Bayesian change-point filter) and a CUSUM statistic, and compare them with the drawdown alone; then evaluate a 10 per cent stop, a two-step de-risking ladder and a posterior-based rule on many simulated paths. End state: a chart of detection delay against false-stop rate for the three rules.
- **Build.** `firm.ddrules`: drawdown rules as objects (stop-loss, ladder, time stop, posterior rule, restart rule), the change-point posterior, and an evaluator on simulated paths (expected P&L, false stops per hundred strategy-years, detection delay of a dead strategy), reusing firm.multistrat's stop_rate and firm.perf's drawdowns; Python.
- **Weekend problem.** Down eight in March -- named result: the posterior probability that a strategy is broken after a given drawdown, and the detection delay of the posterior rule at the false-stop rate of a 10 per cent stop-loss.
- **Facts to verify.** Magdon-Ismail, Atiya, Pratap and Abu-Mostafa 2004, On the maximum drawdown of a Brownian motion (J. Applied Probability); Grossman and Zhou 1993 (pointer to Book 8 ch. 28); Adams and MacKay 2007, Bayesian online changepoint detection (arXiv); Page 1954, Continuous inspection schemes (Biometrika) (pointer to Book 7 ch. 13); Bailey and Lopez de Prado 2014/2015 on drawdowns and stop-outs.
- **Data.** Synthetic.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Magdon-Ismail, Atiya, Pratap and Abu-Mostafa, On the maximum drawdown of a Brownian motion, Journal of Applied Probability 41(1), 147-161, 2004 | Crossref | https://api.crossref.org/works/10.1239/jap/1077134674 | 2026-09-28 | title, journal, volume, pages | omsources; section 1 |
| F2 | Lorden, Procedures for reacting to a change in distribution, Annals of Mathematical Statistics 42(6), 1897-1908, 1971 (asymptotic detection delay log(ARL)/KL) | Crossref | https://api.crossref.org/works/10.1214/aoms/1177693055 | 2026-09-28 | title, journal, volume, pages | prop:fm:managing-a-book-through-drawdown:lorden; omsources |
| F3 | Adams and MacKay, Bayesian online changepoint detection, arXiv:0710.3742, 2007 | arXiv | https://arxiv.org/abs/0710.3742 | 2026-09-28 | title | section 3; omsources |

## EXCLUDED

