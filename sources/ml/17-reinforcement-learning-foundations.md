# 17. Reinforcement Learning Foundations — brief and source ledger

## Brief

- **Hook.** An agent learns to sell a block of shares by trial and error in a simulator and beats the desk's schedule by 3 basis points; in the market the simulator was built from, it loses 5, because what it learned was the simulator.
- **Sections.** Markov decision processes and the Bellman equations; Value methods: temporal differences and Q-learning; Policy methods: gradients and actor-critic; Bandits and exploration; Off-policy evaluation and the simulator problem.
- **Defines.** reinforcement learning, Markov decision process, policy, reward, cumulative reward, action-value function, Bellman equation, temporal-difference learning, Q-learning, policy gradient, actor--critic method, exploration--exploitation trade-off, multi-armed bandit, contextual bandit, off-policy evaluation, doubly robust estimator, sim-to-real gap.
- **Uses (defined earlier).** dynamic programming (B4.9), value function (B4.9), stochastic control problem (B4.9), feedback control (B4.9), Hamilton--Jacobi--Bellman equation (B4.9), Markov chain (B4.8), importance sampling (B4.26), Monte Carlo method (B4.26), stochastic gradient descent (B4.24), effective sample size (B4.14), neural network (ch7), simulator calibration (B7.19).
- **Tutorial.** Solve a small inventory-liquidation MDP exactly by dynamic programming (Book 4), then learn it by tabular Q-learning, SARSA and REINFORCE and track the value gap to the optimum against episodes; evaluate a new policy from logged data by importance sampling, weighted importance sampling and a doubly robust estimator against the truth; train in a mis-specified simulator and evaluate in the true one. Data: synthetic MDPs.
- **Build.** `firm.rlcore`: finite MDPs with exact dynamic-programming solutions, a small environment protocol (reset(seed), step(action)), tabular Q-learning and SARSA, REINFORCE and a small actor-critic, epsilon-greedy and UCB bandits, and off-policy estimators (IS, WIS, doubly robust); Python on NumPy and PyTorch.
- **Weekend problem.** Learning to sell -- named result: Q-learning's value gap to the dynamic-programming optimum after 10,000 episodes, and the bias and spread of the three off-policy estimators.
- **Facts to verify.** Sutton and Barto 2018 Reinforcement Learning: An Introduction (2nd ed.); Watkins and Dayan 1992 Q-learning (Machine Learning); Williams 1992 REINFORCE (Machine Learning); Bellman 1957 Dynamic Programming; Auer, Cesa-Bianchi and Fischer 2002 UCB (Machine Learning); Dudik, Langford and Li 2011 doubly robust policy evaluation (ICML); Precup, Sutton and Singh 2000 eligibility traces for off-policy evaluation (ICML); Mnih et al. 2015 human-level control through deep reinforcement learning (Nature).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | C. J. C. H. Watkins, P. Dayan, "Q-learning", Machine Learning 8 1992 | Crossref/OpenAlex record | https://doi.org/10.1007/BF00992698 | 2026-09-25 | title, journal, year as registered | def. Q-learning; omsources |
| F2 | R. J. Williams, "Simple statistical gradient-following algorithms for connectionist reinforcement learning", Machine Learning 8 1992 (REINFORCE) | Crossref/OpenAlex record | https://doi.org/10.1007/BF00992696 | 2026-09-25 | title, journal, year as registered | def. policy gradient; omsources |
| F3 | P. Auer, N. Cesa-Bianchi, P. Fischer, "Finite-time analysis of the multiarmed bandit problem", Machine Learning 47 2002 (UCB) | Crossref/OpenAlex record | https://doi.org/10.1023/A:1013689704352 | 2026-09-25 | title, journal, year as registered | sec. bandits; omsources |
| F4 | M. Dudík, J. Langford, L. Li, "Doubly robust policy evaluation and learning", arXiv:1103.4601 2011 | arXiv API | https://arxiv.org/abs/1103.4601 | 2026-09-25 | title and abstract | def. doubly robust estimator; omsources |
| F5 | N. Jiang, L. Li, "Doubly robust off-policy value evaluation for reinforcement learning", arXiv:1511.03722 2016 (the per-decision form used in the code) | arXiv API | https://arxiv.org/abs/1511.03722 | 2026-09-25 | title and abstract | listing lst:ml:rl:dr; omsources |
| F6 | V. Mnih et al., "Human-level control through deep reinforcement learning", Nature 518 2015 | Crossref/OpenAlex record | https://doi.org/10.1038/nature14236 | 2026-09-25 | title, journal, year as registered | sec. policy methods; omsources |

## EXCLUDED

- The hook's 0.9 and 0.6 basis points and every cost, gap, regret and estimate are the chapter's liquidation MDP and learners (firm.rlcore, ml_rl), tested in code/ml/17-reinforcement-learning-foundations/tests/test_solutions.py.
- Sutton and Barto 2018 (2nd edition, MIT Press): cited as a textbook; the registry returns only a 1998 review of the first edition, and no fact in the chapter rests on it.
- Bellman 1957 Dynamic Programming and Precup, Sutton and Singh 2000: planned, not cited (dynamic programming is Book 4 chapter 9's; the per-decision estimator cites Jiang and Li).
