# 16. Vectorised Backtests — brief and source ledger

## Brief

- **Hook.** A one-line backtest shows a Sharpe ratio of 3.1. The positions were computed from today's close and multiplied by today's return.
- **Sections.** The vectorised backtest; Four fidelity levels; Where the vectorised backtest is right; The lies it tells; A checklist.
- **Defines.** backtest, fidelity level, vectorised backtest, decision time, execution lag, portfolio turnover, linear cost model, rebalance frequency.
- **Uses (defined earlier).** gross exposure (B1.7), net exposure (B1.7), borrow fee (B1.6), locate (B1.6), short sale (B1.6), closing price (B1.13), Sharpe ratio (B4.11), look-ahead bias (ch3), survivorship bias (ch3), tradable universe (ch4), composite signal (ch14).
- **Tutorial.** Backtest a reversal signal on firm.synthmkt in one vectorised pass, then correct its five lies one at a time (lag, universe, costs, borrow, compounding and cash) and draw the Sharpe-ratio waterfall.
- **Build.** `firm.vecbt`: level-1 backtester (weights or signals, enforced execution lag, universe mask, linear costs and borrow, cash and financing, per-name caps) returning the standard BacktestResult consumed by firm.perf; Python.
- **Weekend problem.** Sharpe 3.1 on Monday, 0.4 on Friday — named result: the Sharpe waterfall from the naive to the honest level-1 backtest, lie by lie.
- **Facts to verify.** Bailey et al. 2014 (Notices AMS); Arnott, Harvey, Markowitz 2019 (JFDS); Novy-Marx and Velikov 2016, a taxonomy of anomalies and their trading costs (RFS).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | R. Novy-Marx, M. Velikov, "A taxonomy of anomalies and their trading costs", Review of Financial Studies 29(1) (2016) 104-147: a buy/hold spread is the most effective cost mitigation; most anomalies with less than 50% monthly turnover generate significant net spreads when designed to mitigate costs, few with higher turnover do; costs always reduce profitability | OpenAlex record with abstract; NBER working paper 20721; Crossref record | https://doi.org/10.1093/rfs/hhv063 | 2026-09-24 | "Most anomalies with less than 50% turnover per month generate significant net spreads when designed to mitigate transaction costs; few with higher turnover do"; "Introducing a buy/hold spread ... is the most effective cost mitigation technique" | section 4; pb 16, 19; omsources |
| F2 | R. Arnott, C. R. Harvey, H. Markowitz, "A backtesting protocol in the era of machine learning", J. Financial Data Science 1(1) (2019) 64-74: machine learning applications often require far more data than are available in finance | OpenAlex record with abstract; Crossref record | https://doi.org/10.3905/jfds.2019.1.064 | 2026-09-24 | "Machine learning applications often require far more data than are available in finance" | section 5; omsources |

## EXCLUDED

- Bailey, Borwein, Lopez de Prado and Zhu (2014): already recorded (bibliographic only) in chapter 1; backtest overfitting is chapter 20's topic, so not cited here.
- The closing-auction order deadlines and borrow-fee levels are referenced to Book 1 (chapters 13 and 6), not restated with new facts; the 50 bp borrow and 10 bp cost are the chapter's assumptions, not market facts.
- All Sharpe ratios, turnovers, break-even costs and capital paths are computed on firm.synthmkt and tested.
