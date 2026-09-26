"""firm.rlcore -- reinforcement learning on small problems with known answers (Book 12, chapter 17).

Finite Markov decision processes solved exactly by backward induction, an environment protocol (reset(seed),
step(u) -> (x, g, done)), tabular Q-learning and SARSA, REINFORCE and a one-step actor-critic with softmax policies,
epsilon-greedy and UCB bandits, and off-policy estimators (importance sampling, weighted importance sampling, doubly
robust). The running example is liquidating a block of shares over a few periods when liquidity switches between two
states. Notation as in the book: state x, action u, reward g, policy pi; horizons are finite and undiscounted.

API (stable):
    liquidation_mdp(T, Q, eta, p_stay, phi, drain) -> FiniteMDP   states (t, q, liquidity); action = lots sold
    FiniteMDP(n_states, n_actions, actions, step_dist, reward, start, time): .actions(s), .reward(s, u),
               .step_dist(s, u) -> [(s', prob)], .start, .solve() -> (V, pi), .q_values(V),
               .evaluate(pi) -> V (pi: array of actions, or (n_states, n_actions) probabilities)
    MDPEnv(mdp).reset(seed) -> x ; .step(u) -> (x', g, done)
    q_learning(env, episodes, alpha, eps, seed) / sarsa(...) -> Q ; greedy(mdp, Q) -> pi
    reinforce(env, episodes, lr, seed) / actor_critic(env, episodes, lr_pi, lr_v, seed) -> theta (softmax preferences)
                                 every learner takes on_episode(n, table), called after each episode (snapshots)
    softmax_policy(mdp, theta) -> probabilities
    bandit(means, sd, n, rule, seed, eps, c) -> (choices, regret)          rule 'eps' or 'ucb'
    rollouts(mdp, pi, n, seed) -> episodes [(s, u, g, prob of u)]
    ope_is, ope_wis, ope_dr(episodes, pi_e, mdp, Q_hat, V_hat)            estimates of the target policy's value
"""
from __future__ import annotations

import numpy as np


class FiniteMDP:
    """A finite-horizon MDP given by functions of an integer state; terminal states have no actions."""

    def __init__(self, n_states, n_actions, actions, step_dist, reward, start, time):
        self.n_states, self.n_actions, self.start = n_states, n_actions, start
        self.actions, self.step_dist, self.reward, self.time = actions, step_dist, reward, time
        self.order = sorted(range(n_states), key=time, reverse=True)       # backward in time

    def solve(self):
        """Backward induction: V*(s) = max_u [ g(s, u) + sum_s' P(s'|s, u) V*(s') ]."""
        V, pi = np.zeros(self.n_states), np.zeros(self.n_states, dtype=int)
        for s in self.order:
            acts = self.actions(s)
            if not acts:
                continue
            q = [self.reward(s, u) + sum(p * V[s2] for s2, p in self.step_dist(s, u)) for u in acts]
            k = int(np.argmax(q))
            V[s], pi[s] = q[k], acts[k]
        return V, pi

    def q_values(self, V):
        Q = np.full((self.n_states, self.n_actions), -np.inf)
        for s in range(self.n_states):
            for u in self.actions(s):
                Q[s, u] = self.reward(s, u) + sum(p * V[s2] for s2, p in self.step_dist(s, u))
        return Q

    def evaluate(self, pi):
        """Exact value of a deterministic (array of actions) or stochastic ((states, actions) probabilities) policy."""
        V = np.zeros(self.n_states)
        for s in self.order:
            acts = self.actions(s)
            if not acts:
                continue
            probs = {u: float(pi[s] == u) for u in acts} if np.ndim(pi) == 1 else {u: pi[s, u] for u in acts}
            V[s] = sum(pr * (self.reward(s, u) + sum(p * V[s2] for s2, p in self.step_dist(s, u)))
                       for u, pr in probs.items() if pr > 0)
        return V


def liquidation_mdp(T=10, Q=10, eta=(0.5, 2.0), p_stay=0.8, phi=0.2, drain=0.0):
    """Sell Q lots in T periods. State (t, q, l): period, lots left, liquidity (0 deep, 1 thin). Selling u lots costs
    eta[l] u^2 basis points (temporary impact); holding q lots after the sale costs phi q^2 (risk); everything left is
    sold in the last period. Liquidity stays the same with probability p_stay, except that each lot sold raises the
    probability that the next period is thin by `drain` (the seller's own trades use up liquidity). Rewards are minus
    costs."""
    L = len(eta)
    n = (T + 1) * (Q + 1) * L

    def idx(t, q, liq):
        return (t * (Q + 1) + q) * L + liq

    def unpack(s):
        return s // ((Q + 1) * L), (s // L) % (Q + 1), s % L

    def actions(s):
        t, q, _ = unpack(s)
        if t == T:
            return []
        if t == T - 1:
            return [q]
        return list(range(q + 1))

    def step_dist(s, u):
        t, q, liq = unpack(s)
        thin = min(1.0, (p_stay if liq == 1 else 1 - p_stay) + drain * u)
        return [(idx(t + 1, q - u, 0), 1 - thin), (idx(t + 1, q - u, 1), thin)]

    def reward(s, u):
        t, q, liq = unpack(s)
        return -(eta[liq] * u**2 + phi * (q - u) ** 2)

    m = FiniteMDP(n, Q + 1, actions, step_dist, reward, idx(0, Q, 0), lambda s: unpack(s)[0])
    m.idx, m.unpack, m.T, m.Q = idx, unpack, T, Q
    return m


class MDPEnv:
    def __init__(self, mdp):
        self.mdp = mdp

    def reset(self, seed=None):
        self.rng = np.random.default_rng(seed)
        self.s = self.mdp.start
        return self.s

    def step(self, u):
        g = self.mdp.reward(self.s, u)
        nxt = self.mdp.step_dist(self.s, u)
        k = self.rng.choice(len(nxt), p=[p for _, p in nxt])
        self.s = nxt[k][0]
        return self.s, g, not self.mdp.actions(self.s)


def _eps_greedy(rng, Q, s, acts, eps):
    if rng.random() < eps:
        return acts[rng.integers(len(acts))]
    return acts[int(np.argmax(Q[s, acts]))]


def q_learning(env, episodes, alpha=0.1, eps=0.1, seed=0, sarsa=False, on_episode=None):
    """Tabular Q-learning (off-policy target max_u' Q(x', u')) or SARSA (on-policy target Q(x', u'))."""
    mdp, rng = env.mdp, np.random.default_rng(seed)
    Q = np.zeros((mdp.n_states, mdp.n_actions))
    for ep in range(episodes):
        s = env.reset(seed * 1_000_003 + ep)
        u = _eps_greedy(rng, Q, s, mdp.actions(s), eps)
        done = False
        while not done:
            s2, g, done = env.step(u)
            if done:
                target, u2 = g, None
            else:
                acts2 = mdp.actions(s2)
                u2 = _eps_greedy(rng, Q, s2, acts2, eps)
                target = g + (Q[s2, u2] if sarsa else Q[s2, acts2].max())
            Q[s, u] += alpha * (target - Q[s, u])
            s, u = s2, u2
        if on_episode:
            on_episode(ep + 1, Q)
    return Q


def sarsa(env, episodes, alpha=0.1, eps=0.1, seed=0, on_episode=None):
    return q_learning(env, episodes, alpha, eps, seed, sarsa=True, on_episode=on_episode)


def greedy(mdp, Q):
    pi = np.zeros(mdp.n_states, dtype=int)
    for s in range(mdp.n_states):
        acts = mdp.actions(s)
        if acts:
            pi[s] = acts[int(np.argmax(Q[s, acts]))]
    return pi


def _probs(theta, s, acts):
    z = theta[s, acts] - theta[s, acts].max()
    e = np.exp(z)
    return e / e.sum()


def softmax_policy(mdp, theta):
    P = np.zeros((mdp.n_states, mdp.n_actions))
    for s in range(mdp.n_states):
        acts = mdp.actions(s)
        if acts:
            P[s, acts] = _probs(theta, s, acts)
    return P


def _sample(rng, P, s, acts):
    return acts[rng.choice(len(acts), p=P[s, acts] / P[s, acts].sum())]


def reinforce(env, episodes, lr=0.05, seed=0, on_episode=None):
    """Monte Carlo policy gradient with softmax preferences: theta(x, .) += lr (G_t - b(x)) grad log pi(u_t | x_t),
    with b(x) the running mean of the return observed from x (a baseline that lowers the variance)."""
    mdp, rng = env.mdp, np.random.default_rng(seed)
    theta, b, nb = np.zeros((mdp.n_states, mdp.n_actions)), np.zeros(mdp.n_states), np.zeros(mdp.n_states)
    for ep in range(episodes):
        s, traj, done = env.reset(seed * 1_000_003 + ep), [], False
        while not done:
            acts = mdp.actions(s)
            u = acts[rng.choice(len(acts), p=_probs(theta, s, acts))]
            s2, g, done = env.step(u)
            traj.append((s, u, g))
            s = s2
        G = 0.0
        for s, u, g in reversed(traj):
            G += g
            nb[s] += 1
            b[s] += (G - b[s]) / nb[s]
            acts = mdp.actions(s)
            grad = -_probs(theta, s, acts)
            grad[acts.index(u)] += 1.0
            theta[s, acts] += lr * (G - b[s]) * grad
        if on_episode:
            on_episode(ep + 1, theta)
    return theta


def actor_critic(env, episodes, lr_pi=0.05, lr_v=0.1, seed=0, on_episode=None):
    """One-step actor-critic: the critic learns V by temporal differences, the actor moves along delta grad log pi."""
    mdp, rng = env.mdp, np.random.default_rng(seed)
    theta, V = np.zeros((mdp.n_states, mdp.n_actions)), np.zeros(mdp.n_states)
    for ep in range(episodes):
        s, done = env.reset(seed * 1_000_003 + ep), False
        while not done:
            acts = mdp.actions(s)
            p = _probs(theta, s, acts)
            k = rng.choice(len(acts), p=p)
            s2, g, done = env.step(acts[k])
            delta = g + (0.0 if done else V[s2]) - V[s]
            V[s] += lr_v * delta
            grad = -p
            grad[k] += 1.0
            theta[s, acts] += lr_pi * delta * grad
            s = s2
        if on_episode:
            on_episode(ep + 1, theta)
    return theta


# ---------------------------------------------------------------------------------------------------- bandits
def bandit(means, sd=1.0, n=10000, rule="ucb", seed=0, eps=0.1, c=2.0):
    """k-armed Gaussian bandit. 'eps': epsilon-greedy; 'ucb': mean + c * sd * sqrt(log t / n_a) (UCB1 scaled by the
    noise). Returns the arms chosen and the cumulative regret (sum of the best mean minus the chosen mean)."""
    rng = np.random.default_rng(seed)
    k = len(means)
    cnt, tot = np.zeros(k), np.zeros(k)
    choices = np.empty(n, dtype=int)
    for t in range(n):
        if t < k:
            a = t
        elif rule == "eps":
            a = int(rng.integers(k)) if rng.random() < eps else int(np.argmax(tot / cnt))
        else:
            a = int(np.argmax(tot / cnt + c * sd * np.sqrt(np.log(t + 1) / cnt)))
        x = means[a] + sd * rng.standard_normal()
        cnt[a] += 1
        tot[a] += x
        choices[t] = a
    regret = np.cumsum(max(means) - np.asarray(means)[choices])
    return choices, regret


# ---------------------------------------------------------------------------------------------------- off-policy
def rollouts(mdp, P, n, seed=0):
    """Episodes of a stochastic policy P (states x actions): lists of (x, u, g, P(u|x))."""
    env, rng, out = MDPEnv(mdp), np.random.default_rng(seed), []
    for i in range(n):
        s, done, ep = env.reset(seed * 1_000_003 + i), False, []
        while not done:
            acts = mdp.actions(s)
            u = _sample(rng, P, s, acts)
            s2, g, done = env.step(u)
            ep.append((s, u, g, P[s, u]))
            s = s2
        out.append(ep)
    return out


def ope_is(episodes, Pe):
    """Per-decision importance sampling: sum_t g_t prod_{k<=t} pi_e(u_k|x_k) / pi_b(u_k|x_k), averaged."""
    vals = []
    for ep in episodes:
        w, v = 1.0, 0.0
        for s, u, g, pb in ep:
            w *= Pe[s, u] / pb
            v += w * g
        vals.append(v)
    return float(np.mean(vals))


def ope_wis(episodes, Pe):
    """Weighted importance sampling: whole-episode weights normalised to sum to one."""
    w = np.array([np.prod([Pe[s, u] / pb for s, u, _, pb in ep]) for ep in episodes])
    G = np.array([sum(g for _, _, g, _ in ep) for ep in episodes])
    return float((w * G).sum() / w.sum()) if w.sum() > 0 else float("nan")


def ope_dr(episodes, Pe, Q_hat, V_hat):
    """Doubly robust (Jiang and Li's per-decision form of Dudik, Langford and Li): a model's value corrected by
    importance-weighted residuals; unbiased if either the weights or the model are right."""
    vals = []
    for ep in episodes:
        w_prev, v = 1.0, 0.0
        for s, u, g, pb in ep:
            w = w_prev * Pe[s, u] / pb
            v += w * (g - Q_hat[s, u]) + w_prev * V_hat[s]
            w_prev = w
        vals.append(v)
    return float(np.mean(vals))
