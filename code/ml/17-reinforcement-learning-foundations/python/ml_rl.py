"""Reinforcement learning foundations (One Quant Book 12, chapter 17).

Liquidating 10 lots in 10 periods while liquidity switches between deep and thin (firm.rlcore.liquidation_mdp): the
exact optimum by backward induction; Q-learning, SARSA, REINFORCE and an actor-critic learning it from episodes; a
five-armed bandit (epsilon-greedy against UCB); off-policy evaluation of a new policy from a desk's logs (importance
sampling, weighted importance sampling, doubly robust) against the exact value; and a policy learned in a simulator
whose thin-liquidity impact is too low, evaluated in the true problem. Costs are in basis points per lot."""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "rlcore"))
from firm_rlcore import (  # noqa: E402
    MDPEnv,
    actor_critic,
    bandit,
    greedy,
    liquidation_mdp,
    ope_dr,
    ope_is,
    ope_wis,
    q_learning,
    reinforce,
    rollouts,
    sarsa,
    softmax_policy,
)

CHECKS = (100, 300, 1000, 3000, 10000)
SEEDS = (0, 1, 2)


@functools.lru_cache(maxsize=1)
def mdp():
    return liquidation_mdp()


def per_lot(v):
    return -v / mdp().Q


@functools.lru_cache(maxsize=1)
def optimum():
    m = mdp()
    V, pi = m.solve()
    return V, pi


def schedule(policy_fn):
    m = mdp()
    pi = np.zeros(m.n_states, dtype=int)
    for s in range(m.n_states):
        if m.actions(s):
            pi[s] = policy_fn(*m.unpack(s))
    return pi


def twap():
    m = mdp()
    return schedule(lambda t, q, liq: min(q, int(np.ceil(q / (m.T - t)))))


@functools.lru_cache(maxsize=1)
def desk():
    """The desk's schedule: the best schedule that ignores liquidity (optimal for the average impact), a function of
    (t, q) only."""
    avg = liquidation_mdp(eta=(1.25, 1.25), p_stay=0.8)
    _, pi = avg.solve()
    return schedule(lambda t, q, liq: pi[avg.idx(t, q, 0)])


def benchmarks():
    m = mdp()
    V, _ = optimum()
    return {"optimal": per_lot(V[m.start]), "desk": per_lot(m.evaluate(desk())[m.start]),
            "TWAP": per_lot(m.evaluate(twap())[m.start])}


@functools.lru_cache(maxsize=1)
def learning_curves():
    """Value gap to the optimum (basis points per lot) of each learner's policy after 100 ... 10,000 episodes, mean
    over three seeds: the greedy policy of Q for Q-learning and SARSA, the learned softmax policy for the others."""
    m = mdp()
    env = MDPEnv(m)
    vstar = optimum()[0][m.start]
    learners = {"Q-learning": (lambda sd, cb: q_learning(env, CHECKS[-1], 0.1, 0.1, sd, on_episode=cb), "q"),
                "SARSA": (lambda sd, cb: sarsa(env, CHECKS[-1], 0.1, 0.1, sd, on_episode=cb), "q"),
                "REINFORCE": (lambda sd, cb: reinforce(env, CHECKS[-1], 0.01, sd, on_episode=cb), "pi"),
                "actor-critic": (lambda sd, cb: actor_critic(env, CHECKS[-1], 0.05, 0.1, sd, on_episode=cb), "pi")}
    out = {}
    for name, (run, kind) in learners.items():
        gaps = np.zeros((len(SEEDS), len(CHECKS)))
        for i, sd in enumerate(SEEDS):
            def cb(n, table, i=i, kind=kind, gaps=gaps):
                if n in CHECKS:
                    pol = greedy(m, table) if kind == "q" else softmax_policy(m, table)
                    gaps[i, CHECKS.index(n)] = (vstar - m.evaluate(pol)[m.start]) / m.Q
            run(sd, cb)
        out[name] = gaps.mean(0)
    return out


@functools.lru_cache(maxsize=1)
def bandits(n=10000, seeds=20):
    """Five execution algorithms whose mean saving is 0, 0.5, 1.0, 1.2 and 1.5 bp per order, with 5 bp of noise:
    cumulative regret (bp) of epsilon-greedy (0.1, 0.01) and UCB (two constants), mean over 20 seeds, and the share
    of the last 1,000 choices that went to the best algorithm."""
    means = [0.0, 0.5, 1.0, 1.2, 1.5]
    out = {}
    for name, kw in (("epsilon 0.1", {"rule": "eps", "eps": 0.1}), ("epsilon 0.01", {"rule": "eps", "eps": 0.01}),
                     ("UCB, c = 1.41", {"rule": "ucb", "c": 2**0.5}), ("UCB, c = 1", {"rule": "ucb", "c": 1.0})):
        regs, best = [], []
        for sd in range(seeds):
            ch, reg = bandit(means, 5.0, n, seed=sd, **kw)
            regs.append(reg)
            best.append(np.mean(ch[-1000:] == 4))
        out[name] = (np.mean(regs, 0), float(np.mean(best)))
    return out


def behaviour_and_target():
    """The desk logged its schedule with 30% random deviations; the target is the optimal policy with 10% random
    deviations (soft, so that importance weights stay finite)."""
    m = mdp()
    _, pi = optimum()
    dk = desk()

    def soft(p, mix):
        P = np.zeros((m.n_states, m.n_actions))
        for s in range(m.n_states):
            acts = m.actions(s)
            if acts:
                P[s, acts] = mix / len(acts)
                P[s, p[s]] += 1 - mix
        return P

    return soft(dk, 0.3), soft(pi, 0.1)


@functools.lru_cache(maxsize=1)
def model_q():
    """A model of the market with thin-liquidity impact too high (3.0 instead of 2.0) and liquidity too changeable
    (stays with probability 0.6 instead of 0.8): the target policy's action values in that model, for the doubly
    robust estimator."""
    wrong = liquidation_mdp(eta=(0.5, 3.0), p_stay=0.6)
    _, Pe = behaviour_and_target()
    V = wrong.evaluate(Pe)
    Q = wrong.q_values(V)
    Vh = np.array([sum(Pe[s, u] * Q[s, u] for u in wrong.actions(s)) if wrong.actions(s) else 0.0
                   for s in range(wrong.n_states)])
    return np.where(np.isfinite(Q), Q, 0.0), Vh


@functools.lru_cache(maxsize=1)
def off_policy(n_logs=300, reps=100):
    """Bias and standard deviation (bp per lot) of the three estimators over 100 sets of 300 logged episodes."""
    m = mdp()
    Pb, Pe = behaviour_and_target()
    truth = m.evaluate(Pe)[m.start]
    Qh, Vh = model_q()
    est = {"IS": [], "WIS": [], "DR": [], "model": []}
    for r in range(reps):
        eps = rollouts(m, Pb, n_logs, seed=1000 + r)
        est["IS"].append(ope_is(eps, Pe))
        est["WIS"].append(ope_wis(eps, Pe))
        est["DR"].append(ope_dr(eps, Pe, Qh, Vh))
        est["model"].append(Vh[m.start])
    out = {"truth": per_lot(truth), "behaviour": per_lot(m.evaluate(Pb)[m.start])}
    for k, v in est.items():
        v = np.array(v)
        out[k] = (float(np.mean(-v / m.Q) - per_lot(truth)), float(np.std(v / m.Q)))
    return out


@functools.lru_cache(maxsize=1)
def sim_to_real(episodes=10000, seed=0):
    """Q-learning in a simulator whose liquidity alternates every period (p_stay 0 instead of 0.8: a calendar pattern
    in the data it was calibrated on), evaluated in the simulator and in the true problem, against the desk."""
    sim, true = liquidation_mdp(p_stay=0.0), mdp()
    pol = greedy(sim, q_learning(MDPEnv(sim), episodes, 0.1, 0.1, seed))
    dk = desk()
    return {"agent in simulator": per_lot(sim.evaluate(pol)[sim.start]),
            "desk in simulator": per_lot(sim.evaluate(dk)[sim.start]),
            "agent in market": per_lot(true.evaluate(pol)[true.start]),
            "desk in market": per_lot(true.evaluate(dk)[true.start]),
            "optimal in market": per_lot(optimum()[0][true.start])}
