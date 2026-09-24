# 9. Stochastic Control — brief and source ledger

## Brief

- **Hook.** After a 20% equity fall a pension fund's equity weight has drifted from 60% to 52%; its rulebook says buy back to 60% at quarter-end, and half the committee wants to wait. For an investor with constant relative risk aversion in a lognormal market the committee's rulebook is exactly right.
- **Sections.** Dynamic programming; The Hamilton--Jacobi--Bellman equation; Verification; Merton's problem; A sketch of viscosity solutions.
- **Defines.** stochastic control problem, admissible control, value function, dynamic programming, feedback control, Hamilton--Jacobi--Bellman equation, utility function, relative risk aversion, CRRA utility, Merton fraction, certainty equivalent, viscosity solution.
- **Uses (defined earlier).** Kelly criterion, growth rate, infinitesimal generator, geometric Brownian motion, Itô's formula (result), stochastic differential equation, martingale, supermartingale.
- **Results (named theorems, not terms).** dynamic programming principle; verification theorem; Merton's solution (constant fraction, optimal consumption); log utility gives the Kelly fraction (link to Book 2 ch. 29); a value function that is continuous but not differentiable (example).
- **Tutorial.** Solve a discrete-time Merton problem by backward induction on a wealth grid, compare the optimal fraction with the closed form, and measure the certainty-equivalent cost of fixed allocations.
- **Build.** `firm.dpsolve`: finite-horizon dynamic programming on grids (backward induction with interpolation, controls on a grid or by golden-section search, policy extraction); Python.
- **Weekend problem.** The rebalancing committee — named result: the Merton fraction for the fund's assumptions and the certainty-equivalent return lost per year by holding 60% instead.
- **Facts to verify.** Merton 1969 (Review of Economics and Statistics) lifetime portfolio selection; Merton 1971 (Journal of Economic Theory); Bellman 1957, Dynamic Programming; Crandall and Lions 1983 (Trans. AMS) viscosity solutions; Samuelson 1969 discrete-time counterpart.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | R. C. Merton, "Lifetime portfolio selection under uncertainty: the continuous-time case", Review of Economics and Statistics 51(3) (1969), 247-257: optimal portfolio and consumption in continuous time, explicit for constant relative risk aversion | RePEc/IDEAS record | https://ideas.repec.org/a/tpr/restat/v51y1969i3p247-57.html | 2026-09-24 | "particular attention to the two-asset model with constant relative risk-aversion" | hook; thm Merton; omsources |
| F2 | P. A. Samuelson, "Lifetime portfolio selection by dynamic stochastic programming", Review of Economics and Statistics 51(3) (1969), 239-246 (the discrete-time companion) | RePEc/IDEAS record | https://ideas.repec.org/a/tpr/restat/v51y1969i3p239-46.html | 2026-09-24 | REStat 51(3), 239-246 | omsources |
| F3 | R. Bellman, Dynamic Programming, Princeton University Press, 1957 | Science review record | https://www.science.org/doi/10.1126/science.127.3304.976.a | 2026-09-24 | "Dynamic Programming. Richard Bellman. Princeton University Press, Princeton, N.J., 1957" | omsources |
| F4 | M. G. Crandall and P.-L. Lions, "Viscosity solutions of Hamilton-Jacobi equations", Transactions of the AMS 277 (1983), 1-42 | AMS journal PDF | https://www.ams.org/journals/tran/1983-277-01/S0002-9947-1983-0690039-8/S0002-9947-1983-0690039-8.pdf | 2026-09-24 | Trans. AMS 277 (1983) 1-42 | §5; omsources |
| F5 | W. H. Fleming and H. M. Soner, Controlled Markov Processes and Viscosity Solutions, Springer, 2nd ed. 2006 (dynamic programming principle in continuous time) | Springer book record (Stochastic Modelling and Applied Probability 25) | https://link.springer.com/book/10.1007/0-387-31071-1 | 2026-09-24 | 2nd edition, 2006 | partial proof of the DPP; omsources |

## EXCLUDED

- Merton 1971 (JET) not cited in the text.
- The fund's inputs (mu 7%, r 2%, sigma 18%, gamma 3) are the problem's assumptions, not market facts.

