# 8. Markov Chains and Queues — brief and source ledger

## Brief

- **Hook.** At the best bid of a large-tick future sit 800 lots; a market maker has just joined the back of the queue and asks what chance its order has of filling before the bid queue is eaten and the price ticks down.
- **Sections.** Continuous-time Markov chains; Birth--death processes and simple queues; Hitting probabilities and hitting times; Queues sized for order books.
- **Defines.** Markov chain, continuous-time Markov chain, generator matrix, jump chain, detailed balance, birth--death process, M/M/1 queue, absorbing state, hitting probability, first-step analysis.
- **Uses (defined earlier).** Poisson process, Markov process, stationary distribution, stopping time, martingale, price-time priority, order, mid price, market-by-order.
- **Results (named theorems, not terms).** Kolmogorov equations for finite chains; convergence to the stationary distribution (irreducible finite chain); Little's law; probability that the bid queue depletes before the ask queue (Cont-de Larrard).
- **Tutorial.** Model the best bid and best ask queues as birth-death processes; compute the probability that the next mid move is up as a function of the two queue sizes by solving the hitting-probability linear system, and check it against simulation and against a queue-imbalance heuristic.
- **Build.** `firm.queues`: finite continuous-time Markov chains (generator, stationary law, hitting probabilities and expected hitting times by sparse linear solve), birth-death queues, next-move and fill probabilities from queue position; Python.
- **Weekend problem.** The back of the queue — named result: the probability that an order joining the back of an 800-lot bid queue fills before the price moves away, and its expected waiting time, for given limit, cancel and market-order rates.
- **Facts to verify.** Cont, Stoikov and Talreja 2010 (Operations Research) order-book model; Cont and de Larrard 2013 (SIAM J. Financial Mathematics) Markovian limit order market; Little 1961 (Operations Research); Kendall 1953 notation; Erlang 1909.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | R. Cont, S. Stoikov and R. Talreja, "A stochastic model for order book dynamics", Operations Research 58(3) (2010), 549-563: a continuous-time Markov model of the limit order book with Laplace-transform computation of price-move and fill probabilities | EconPapers record | https://econpapers.repec.org/RePEc:inm:oropre:v:58:y:2010:i:3:p:549-563 | 2026-09-24 | Operations Research 58(3), 549-563 | omsources |
| F2 | R. Cont and A. de Larrard, "Price dynamics in a Markovian limit order market", SIAM Journal on Financial Mathematics 4(1) (2013), 1-25: price moves as races between the depletion of the best queues | arXiv 1104.4596 | https://arxiv.org/pdf/1104.4596 | 2026-09-24 | SIAM J. Financial Math. 4(1), 1-25 | hook; §4; omsources |
| F3 | J. D. C. Little, "A proof for the queuing formula L = lambda W", Operations Research 9(3) (1961), 383-387 | INFORMS record, doi 10.1287/opre.9.3.383 | https://pubsonline.informs.org/doi/10.1287/opre.9.3.383 | 2026-09-24 | "if the three means are finite and the corresponding stochastic processes strictly stationary ... then L = lambda W" | §2 Little's law; omsources |
| F4 | D. G. Kendall, "Stochastic processes occurring in the theory of queues and their analysis by the method of the imbedded Markov chain", Annals of Mathematical Statistics 24(3) (1953), 338-354 (origin of the A/B/c notation) | Project Euclid record, doi 10.1214/aoms/1177728975 | https://projecteuclid.org/journals/annals-of-mathematical-statistics/volume-24/issue-3/Stochastic-Processes-Occurring-in-the-Theory-of-Queues-and-their/10.1214/aoms/1177728975.full | 2026-09-24 | Ann. Math. Statist. 24(3), 338-354 | def M/M/1 (Kendall's notation); omsources |

## EXCLUDED

- Erlang 1909 (planned): not cited.
- The order-flow rates (0.9 joins, 0.6 market, 0.4 cancels per second, 10-lot orders) are the problem's illustrative choices, not measured facts about a named contract.

