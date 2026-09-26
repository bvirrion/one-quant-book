import itertools
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_rlcore import (  # noqa: E402
    MDPEnv,
    bandit,
    greedy,
    liquidation_mdp,
    ope_dr,
    ope_is,
    ope_wis,
    q_learning,
    rollouts,
)


def _all_plans(m):
    """Brute force for a deterministic-liquidity MDP (p_stay = 1): enumerate every sale sequence."""
    best = -np.inf
    for plan in itertools.product(range(m.Q + 1), repeat=m.T - 1):
        if sum(plan) > m.Q:
            continue
        s, v = m.start, 0.0
        for u in list(plan) + [None]:
            t, q, _ = m.unpack(s)
            u = q if u is None else u
            v += m.reward(s, u)
            s = m.step_dist(s, u)[0][0] if m.step_dist(s, u)[0][1] > 0 else m.step_dist(s, u)[1][0]
        best = max(best, v)
    return best


def test_backward_induction_matches_brute_force():
    m = liquidation_mdp(T=4, Q=4, p_stay=1.0)
    V, _ = m.solve()
    assert abs(V[m.start] - _all_plans(m)) < 1e-9


def test_exact_evaluation_matches_monte_carlo():
    m = liquidation_mdp(T=5, Q=5)
    _, pi = m.solve()
    env, tot = MDPEnv(m), []
    for i in range(4000):
        s, done, g_sum = env.reset(i), False, 0.0
        while not done:
            s, g, done = env.step(int(pi[s]))
            g_sum += g
        tot.append(g_sum)
    assert abs(np.mean(tot) - m.evaluate(pi)[m.start]) < 3 * np.std(tot) / np.sqrt(len(tot))


def test_q_learning_finds_the_optimum_on_a_small_problem():
    m = liquidation_mdp(T=4, Q=4)
    V, _ = m.solve()
    pol = greedy(m, q_learning(MDPEnv(m), 5000, 0.1, 0.2, seed=0))
    assert m.evaluate(pol)[m.start] > V[m.start] - 0.05


def _policies(m):
    Pb, Pe = np.zeros((m.n_states, m.n_actions)), np.zeros((m.n_states, m.n_actions))
    _, pi = m.solve()
    for s in range(m.n_states):
        acts = m.actions(s)
        if acts:
            Pb[s, acts] = 1 / len(acts)
            Pe[s, acts] = 0.2 / len(acts)
            Pe[s, pi[s]] += 0.8
    return Pb, Pe


def _model(m, Pe):
    Q = m.q_values(m.evaluate(Pe))
    Vh = np.array([sum(Pe[s, u] * Q[s, u] for u in m.actions(s)) if m.actions(s) else 0.0 for s in range(m.n_states)])
    return np.where(np.isfinite(Q), Q, 0.0), Vh


def test_ope_unbiased_and_dr_lower_variance():
    m = liquidation_mdp(T=3, Q=3)
    Pb, Pe = _policies(m)
    truth = m.evaluate(Pe)[m.start]
    eps = rollouts(m, Pb, 20000, seed=1)
    assert abs(ope_is(eps, Pe) - truth) < 0.5 and abs(ope_wis(eps, Pe) - truth) < 0.5
    Qh, Vh = _model(m, Pe)
    reps = [rollouts(m, Pb, 50, seed=10 + r) for r in range(40)]
    dr = [ope_dr(e, Pe, Qh, Vh) for e in reps]
    ips = [ope_is(e, Pe) for e in reps]
    assert abs(np.mean(dr) - truth) < 3 * np.std(dr) / np.sqrt(40) + 1e-9 and np.std(dr) < np.std(ips)


def test_dr_exact_with_true_model_and_deterministic_transitions():
    m = liquidation_mdp(T=3, Q=3, p_stay=1.0)
    Pb, Pe = _policies(m)
    Qh, Vh = _model(m, Pe)
    small = rollouts(m, Pb, 50, seed=2)
    assert abs(ope_dr(small, Pe, Qh, Vh) - m.evaluate(Pe)[m.start]) < 1e-9


def test_ucb_beats_random_choice():
    means = [0.0, 1.0]
    _, reg = bandit(means, 1.0, 2000, rule="ucb", seed=0, c=1.0)
    _, reg_random = bandit(means, 1.0, 2000, rule="eps", seed=0, eps=1.0)
    assert reg[-1] < 0.2 * reg_random[-1]


def test_drain_makes_thin_liquidity_likelier():
    m = liquidation_mdp(drain=0.1)
    s = m.start
    thin = dict((m.unpack(s2)[2], p) for s2, p in m.step_dist(s, 3))[1]
    assert abs(thin - (0.2 + 0.3)) < 1e-12
