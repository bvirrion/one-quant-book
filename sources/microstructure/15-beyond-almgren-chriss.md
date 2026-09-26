# 15. Beyond Almgren--Chriss — brief and source ledger

## Brief

- **Hook.** The Almgren-Chriss schedule does not look at the market while it trades. A trader who expects the price to fall in the next half-hour should sell faster; one whose impact decays should pause after a large trade; one whose market dries up at lunch should trade before it does.
- **Sections.** Execution with a signal; Adaptive schedules; Transient impact and the optimal block; Stochastic liquidity; A control-theory template.
- **Defines.** signal-adaptive schedule, adaptive execution, aggressive-in-the-money strategy, bucket-shaped trajectory, stochastic liquidity.
- **Uses (defined earlier).** Almgren--Chriss model (ch14), trading trajectory (ch14), urgency (ch14), transient impact model (ch12), Obizhaeva--Wang model (ch12), Hamilton--Jacobi--Bellman equation (B4.9), stochastic control problem (B4.9), value function (B4.9), dynamic programming (B4.9), impulse control (B4.10), Ornstein--Uhlenbeck process (B4.4), Kalman filter (B4.19), execution coupling (B8.14), implementation shortfall (B7.19).
- **Tutorial.** Solve execution with an Ornstein-Uhlenbeck alpha signal in closed form (linear-quadratic), the Obizhaeva-Wang optimum with its blocks at both ends, and a stochastic-liquidity schedule by dynamic programming with Book 4's firm.dpsolve; run all three in firm.exchsim against Almgren-Chriss on common random numbers. Data: simulated.
- **Build.** `firm.execcontrol`: linear-quadratic execution with signals (Riccati), the Obizhaeva-Wang optimal schedule, adaptive (aggressive-in-the-money) rules, and a dynamic-programming wrapper for stochastic liquidity, all returning schedules in firm.acexec's scheduler interface; Python.
- **Weekend problem.** Trading on a forecast -- named result: the basis points an alpha signal saves an execution schedule, against the signal's half-life and strength.
- **Facts to verify.** Obizhaeva and Wang 2013 (JFM); Almgren 2012 optimal trading with stochastic liquidity and volatility (SIFIN); Cartea and Jaimungal 2016 incorporating order-flow into optimal execution (Mathematics and Financial Economics); Cartea, Jaimungal, Penalva 2015 Algorithmic and High-Frequency Trading (CUP); Lorenz and Almgren 2011 mean-variance optimal adaptive execution (Applied Mathematical Finance); Gatheral and Schied 2011 optimal trade execution under geometric Brownian motion in the Almgren and Chriss framework (IJTAF).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | A. A. Obizhaeva and J. Wang, "Optimal trading strategy and supply/demand dynamics", Journal of Financial Markets 16(1) (2013) 1-32: optimal execution mixes discrete and continuous trades | Crossref record; SSRN abstract (686168) | https://doi.org/10.1016/j.finmar.2012.09.001 | 2026-09-25 | "the optimal execution strategy involves both discrete and continuous trades" | §3, omsources |
| F2 | R. Almgren, "Optimal trading with stochastic liquidity and volatility", SIAM Journal on Financial Mathematics 3(1) (2012) 163-181: mean-variance optimal agency execution when liquidity and volatility vary randomly; strategies adapt to the instantaneous variations of market quality | Crossref record with abstract | https://doi.org/10.1137/090763470 | 2026-09-25 | "These strategies adapt optimally to the instantaneous variations of market quality." | §4, omsources |
| F3 | A. Cartea and S. Jaimungal, "Incorporating order-flow into optimal execution", Mathematics and Financial Economics 10(3) (2016) 339-364 | Crossref record | https://doi.org/10.1007/s11579-016-0162-z | 2026-09-25 | bibliographic record | §1, omsources |
| F4 | P. Lorenz and R. Almgren, "Mean-variance optimal adaptive execution", Applied Mathematical Finance 18(5) (2011) 395-422 | Crossref record | https://doi.org/10.1080/1350486x.2011.560707 | 2026-09-25 | bibliographic record | §2, omsources |
| F5 | J. Gatheral and A. Schied, "Optimal trade execution under geometric Brownian motion in the Almgren and Chriss framework", International Journal of Theoretical and Applied Finance 14(3) (2011) 353-368: a closed-form optimal strategy for GBM with an alternative risk criterion | Crossref record with abstract | https://doi.org/10.1142/s0219024911006577 | 2026-09-25 | "we solve the HJB equation explicitly to find a closed-form solution for the optimal trade execution strategy in the Almgren-Chriss framework assuming the underlying unaffected stock price process is geometric Brownian motion" | §5, omsources |

## EXCLUDED

- Cartea, Jaimungal and Penalva (2015, Algorithmic and High-Frequency Trading): not needed beyond the paper; not cited.
- The chapter's schedules are compared by Monte Carlo on the model (and chapter 14 ran Almgren-Chriss in firm.exchsim); running each of them in firm.exchsim was left as the tutorial's extension because the market's noise hides differences of a few basis points without hundreds of sessions.
- All numbers are computed by firm.execcontrol and tested.
