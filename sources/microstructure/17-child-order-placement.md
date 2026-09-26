# 17. Child-Order Placement — brief and source ledger

## Brief

- **Hook.** An algorithm must buy 800 shares in the next minute. It can join the queue at the bid and hope, or pay the spread now. Waiting saves half a spread if it fills and costs more than that if the price walks away while it waits.
- **Sections.** The placement problem; Passive against aggressive; Queue management and repricing; Placement as a Markov decision problem; Learning a placement policy.
- **Defines.** order placement problem, non-execution risk, clean-up trade, repricing rule, queue-aware placement.
- **Uses (defined earlier).** limit order (ch1), market order (ch1), queue value (ch6), queue position (B7.18), passive fill probability (B7.18), queue imbalance (B7.8), microprice (B7.8), child order (ch14), adverse selection (B1.1), dynamic programming (B4.9), birth--death process (B4.8), reinforcement learning (B12.17, forward).
- **Tutorial.** On firm.exchsim, compare placement policies for a one-minute slice (join the bid, step one tick behind, cross at once, imbalance-conditioned) by cost per share and its spread; solve the placement problem by dynamic programming on a birth-death book model; train a tabular Q-learning policy and compare it with the dynamic-programming one (forward pointer to Book 12). Data: simulated.
- **Build.** `firm.placement`: placement policies (static offsets, imbalance-conditioned, dynamic programming on a Markov book, a tabular Q-learning baseline), fill-probability models, repricing rules and a slice executor that plugs into firm.algos; Python.
- **Weekend problem.** Join, step ahead or cross? -- named result: the expected cost per share of each placement policy, and the queue-imbalance threshold above which crossing at once is cheaper.
- **Facts to verify.** Cont and Kukanov 2017 optimal order placement in limit order markets (QF); Nevmyvaka, Feng, Kearns 2006 reinforcement learning for optimized trade execution (ICML); Harris and Hasbrouck 1996 market vs limit orders (JFQA); Lehalle and Mounjid 2017 (Market Microstructure and Liquidity); Huang, Lehalle, Rosenbaum 2015 simulating and analyzing order book data: the queue-reactive model (JASA).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | L. Harris and J. Hasbrouck, "Market vs. limit orders: the SuperDOT evidence on order submission strategy", Journal of Financial and Quantitative Analysis 31(2) (1996) 213-231: limit orders at or better than the quote beat market orders even after a penalty for unexecuted orders | Crossref record; RePEc/IDEAS abstract | https://doi.org/10.2307/2331180 ; https://ideas.repec.org/a/cup/jfinqa/v31y1996i02p213-231_00.html | 2026-09-26 | "Limit orders placed at or better than the prevailing quote perform better than do market orders, even after imputing a penalty for unexecuted orders" | §1, omsources |
| F2 | Y. Nevmyvaka, Y. Feng, M. Kearns, "Reinforcement learning for optimized trade execution", Proceedings of ICML 2006, 673-680: reinforcement learning applied to trade execution on NASDAQ limit order data | Crossref record; authors' PDF | https://doi.org/10.1145/1143844.1143929 ; https://www.cis.upenn.edu/~mkearns/papers/rlexec.pdf | 2026-09-26 | "We present the first large-scale empirical application of reinforcement learning to the important problem of optimized trade execution in modern financial markets. Our experiments are based on 1.5 years of millisecond time-scale limit order data from NASDAQ" | §5, omsources |
| F3 | W. Huang, C.-A. Lehalle, M. Rosenbaum, "Simulating and analyzing order book data: the queue-reactive model", Journal of the American Statistical Association 110(509) (2015) 107-122: the book as a Markov queuing system whose intensities depend on the book's state | Crossref record; arXiv abstract (1312.0563) | https://doi.org/10.1080/01621459.2014.982278 ; https://arxiv.org/abs/1312.0563 | 2026-09-26 | "we view the limit order book as a Markov queuing system. Indeed, we assume that the intensities of the order flows only depend on the current state of the order book" | §4, omsources |
| F4 | R. Cont and A. Kukanov, "Optimal order placement in limit order markets", Quantitative Finance 17(1) (2017) 21-39: the placement across venues of limit and market orders as a convex optimisation, with fees and rebates | Crossref record; SSRN abstract (2155218) | https://doi.org/10.1080/14697688.2016.1190030 | 2026-09-26 | "participants in electronic equity markets may choose to submit limit orders or market orders across various exchanges ... We propose a quantitative framework for studying this order placement problem by formulating it as a convex optimization problem" (published online 2016, issue 2017) | §4, omsources |
| F5 | C.-A. Lehalle and O. Mounjid, "Limit order strategic placement with adverse selection risk and the role of latency", Market Microstructure and Liquidity 3(1) (2017) 1750009: limit-order strategies that exploit liquidity imbalance to reduce adverse selection | Crossref record with abstract | https://doi.org/10.1142/S2382626617500095 | 2026-09-26 | "we develop a stochastic control framework where agents monitor limit orders, by exploiting liquidity imbalance, to reduce adverse selection" | §3, omsources |

## EXCLUDED

- The weekend problem's title keeps "step ahead", but stepping ahead hardly exists in the simulated market (one-tick spread 97.7% of the time); the
  chapter says so instead of running a policy that would almost always be crossing or joining.
- Named result, honestly: the queue-imbalance threshold exists in the Markov model only for small, urgent orders (one lot: 0.86 with 15 s, 0.79
  with 5 s, 0.66 with 3 s; never for 8 lots); in the simulated market crossing is never significantly cheaper at any imbalance (paired, one lot, 5 s).
- Markets tuned: a calmer population than chapter 16's (near 0.5, cancel 0.02, noise 0.6) so that queues matter; stronger fundamentalists
  (tested: fund 0.2-0.5, v_rate 0.2-0.5) did not produce a threshold either.
- All numbers are computed by mx_place and firm.placement and tested.

