"""firm.rltrade -- reinforcement learning for execution and market making (Book 12, chapter 18).

Two environments with the rlcore protocol (reset(seed) -> x, step(u) -> (x, g, done)) whose optimal policies are known
in closed form, so that learned policies can be measured against them: Almgren-Chriss liquidation (Book 10's
firm.acexec gives the optimal schedule and its cost and variance) and Cartea-Jaimungal market making (Book 11's
firm.invmm gives the exact optimal depths and a vectorised simulator with common random numbers). A small deep
Q-network with experience replay, a target network and action masking learns the first; tabular Q-learning with a
shaped reward learns the second. Domain randomisation draws the impact parameter anew each episode.

API (stable):
    ACEnv(X, T, n, lots, eta, sigma, lam, eta_range, noise) .reset(seed) .step(u) ; .mask() valid actions
    grid_optimum(env, eta) -> the best holdings on the lot grid (backward induction)
    DQN(d_in, n_actions, hidden) ; train_dqn(env, episodes, seed, ...) -> (net, losses)
    dqn_schedule(env, net) -> holdings x_0..x_n of the greedy policy
    ac_objective(holdings, env, eta) -> expected cost + lam * variance (firm.acexec.cost_var)
    MMEnv(T, dt, sigma, A, k, phi, alpha, qmax, depths, n_time) ; q_learning_mm(env, episodes, seed, ...) -> Q
    mm_policy(env, Q) -> policy(t, q) for firm.invmm.simulate ; mm_objective(result, phi, alpha)
"""
from __future__ import annotations

import collections
import copy
import math
import pathlib
import sys

import numpy as np
import torch
from torch import nn

_FIRM = pathlib.Path(__file__).resolve().parents[1]
for _c in ("acexec", "invmm"):
    sys.path.insert(0, str(_FIRM / _c))
from firm_acexec import cost_var  # noqa: E402


class ACEnv:
    """Sell X over T in n steps, in multiples of X / lots. State (t / n, x / X, impact seen). Reward: minus the impact
    cost eta u^2 / tau of the sale, minus the risk charge lam sigma^2 tau x^2 on the holdings after it; with noise,
    plus the zero-mean P&L of those holdings over the step, sigma sqrt(tau) Z x (leaving it out is a reward shaping
    that keeps the optimum). Everything left is sold at the last step. With eta_range, each episode draws eta
    log-uniformly from it (domain randomisation); the agent learns it only from the cost of its own sales."""

    def __init__(self, X=1.0, T=1.0, n=10, lots=20, eta=0.001, sigma=0.02, lam=10.0, eta_range=None, noise=False):
        self.X, self.T, self.n, self.lots, self.eta, self.sigma, self.lam = X, T, n, lots, eta, sigma, lam
        self.eta_range, self.tau, self.noise = eta_range, T / n, noise

    def reset(self, seed=None):
        self.rng = np.random.default_rng(seed)
        self.k, self.left = 0, self.lots
        self.eta_ep = self.eta if self.eta_range is None else float(np.exp(self.rng.uniform(*np.log(self.eta_range))))
        return self.obs()

    def obs(self):
        """Time, holdings, and the impact learned from the agent's own fills so far: log(eta / eta_model) once a sale
        has been made (the cost of a sale reveals eta), 0 before."""
        seen = math.log(self.eta_ep / self.eta) if self.left < self.lots else 0.0
        return np.array([self.k / self.n, self.left / self.lots, seen], dtype=np.float32)

    def mask(self):
        if self.k == self.n - 1:
            return [self.left]
        return list(range(self.left + 1))

    def step(self, u):
        u = self.left if self.k == self.n - 1 else u
        du, self.left, self.k = u * self.X / self.lots, self.left - u, self.k + 1
        x = self.left * self.X / self.lots
        g = -(self.eta_ep * du**2 / self.tau + self.lam * self.sigma**2 * self.tau * x**2)
        if self.noise:
            g += self.sigma * math.sqrt(self.tau) * self.rng.standard_normal() * x
        return self.obs(), g, self.k == self.n

    def forced(self):
        return self.k == self.n - 1


class DQN(nn.Module):
    def __init__(self, d_in, n_actions, hidden=(64, 64)):
        super().__init__()
        layers, d = [], d_in
        for h in hidden:
            layers += [nn.Linear(d, h), nn.ReLU()]
            d = h
        self.net = nn.Sequential(*layers, nn.Linear(d, n_actions))

    def forward(self, x):
        return self.net(x)


def _mask(left, forced, n_act):
    """Valid actions as a boolean tensor: sell 0..left lots, or exactly `left` at the last step (action masking)."""
    a = torch.arange(n_act)[None, :]
    left, forced = torch.as_tensor(left)[:, None], torch.as_tensor(forced)[:, None]
    return torch.where(forced, a == left, a <= left)


def train_dqn(env, episodes=3000, seed=0, lr=1e-3, batch=64, buffer=20000, target_every=200, eps_end=0.05,
              reward_scale=1e4):
    """Deep Q-learning (Mnih and co-authors) with experience replay, a target network copied every `target_every`
    updates, epsilon decaying linearly to eps_end over the first half, and invalid actions masked in both the
    choice and the target. Rewards are multiplied by reward_scale (basis points for the chapter)."""
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    n_act = env.lots + 1
    net = DQN(3, n_act)
    tgt = copy.deepcopy(net)
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    mem = collections.deque(maxlen=buffer)
    losses, updates = [], 0
    for ep in range(episodes):
        eps = max(eps_end, 1.0 - (1.0 - eps_end) * ep / (episodes / 2))
        x, done = env.reset(seed * 1_000_003 + ep), False
        while not done:
            m = _mask([env.left], [env.forced()], n_act)[0]
            if rng.random() < eps:
                valid = torch.nonzero(m)[:, 0]
                u = int(valid[rng.integers(len(valid))])
            else:
                with torch.no_grad():
                    u = int(net(torch.as_tensor(x)).masked_fill(~m, -1e9).argmax())
            x2, g, done = env.step(u)
            mem.append((x, u, g * reward_scale, x2, done, env.left, env.forced()))
            x = x2
            if len(mem) >= batch:
                b = [mem[i] for i in rng.choice(len(mem), batch, replace=False)]
                X, X2 = torch.as_tensor(np.stack([e[0] for e in b])), torch.as_tensor(np.stack([e[3] for e in b]))
                U = torch.as_tensor([e[1] for e in b])
                G, D = (torch.as_tensor([e[i] for e in b], dtype=torch.float32) for i in (2, 4))
                M2 = _mask([e[5] for e in b], [e[6] for e in b], n_act)
                with torch.no_grad():
                    y = G + (1 - D) * tgt(X2).masked_fill(~M2, -1e9).max(1).values
                loss = nn.functional.smooth_l1_loss(net(X).gather(1, U[:, None])[:, 0], y)
                opt.zero_grad()
                loss.backward()
                opt.step()
                updates += 1
                losses.append(float(loss.detach()))
                if updates % target_every == 0:
                    tgt.load_state_dict(net.state_dict())
    return net, losses


def dqn_schedule(env, net, eta=None):
    """Holdings x_0..x_n under the greedy policy in a world with impact eta (default: the environment's), in one
    pass: the policy depends on time, holdings and the impact it observes, not on the price."""
    env.reset(0)
    env.eta_ep = env.eta if eta is None else eta
    xs = [env.X]
    with torch.no_grad():
        for _ in range(env.n):
            m = _mask([env.left], [env.forced()], env.lots + 1)[0]
            env.step(int(net(torch.as_tensor(env.obs())).masked_fill(~m, -1e9).argmax()))
            xs.append(env.left * env.X / env.lots)
    return np.array(xs)


def grid_optimum(env, eta=None):
    """The best schedule on the environment's lot grid, by backward induction over (step, lots left)."""
    eta = env.eta if eta is None else eta
    L, n, tau = env.lots, env.n, env.tau
    V = np.zeros(L + 1)
    best = []
    for k in range(n - 1, -1, -1):
        V2, choice = np.full(L + 1, np.inf), np.zeros(L + 1, dtype=int)
        for left in range(L + 1):
            for u in ([left] if k == n - 1 else range(left + 1)):
                x = (left - u) * env.X / L
                c = eta * (u * env.X / L) ** 2 / tau + env.lam * env.sigma**2 * tau * x**2 + V[left - u]
                if c < V2[left]:
                    V2[left], choice[left] = c, u
        V = V2
        best.append(choice)
    best = best[::-1]
    xs, left = [env.X], L
    for k in range(n):
        left -= best[k][left]
        xs.append(left * env.X / L)
    return np.array(xs)


def ac_objective(holdings, env, eta):
    """Expected temporary-impact cost plus lam times the variance, for impact eta (no permanent impact)."""
    e, v = cost_var(holdings, env.T, 0.0, eta, env.sigma)
    return e + env.lam * v


# ---------------------------------------------------------------------------------------------------- market making
class MMEnv:
    """The Cartea-Jaimungal market-making model stepped at dt: quote depths (delta_b, delta_a) from a grid, fills
    with probability A exp(-k delta) dt per side, inventory in [-qmax, qmax] (the side that would breach is masked).
    Shaped reward per step: spread earned on fills minus phi q^2 dt, and minus alpha q^2 at the end; the zero-mean
    term q dS is left out (its expectation is zero, so the optimal policy is unchanged)."""

    def __init__(self, T=1.0, dt=0.005, sigma=2.0, A=140.0, k=1.5, phi=0.02, alpha=0.01, qmax=10,
                 depths=(0.4, 0.55, 0.7, 0.85, 1.0, 1.3), n_time=20):
        self.T, self.dt, self.sigma, self.A, self.k = T, dt, sigma, A, k
        self.phi, self.alpha, self.qmax = phi, alpha, qmax
        self.depths, self.n_time, self.n = np.array(depths), n_time, int(round(T / dt))
        self.actions = [(i, j) for i in range(len(depths)) for j in range(len(depths))]

    def state(self, i, q):
        return min(self.n_time - 1, i * self.n_time // self.n) * (2 * self.qmax + 1) + (q + self.qmax)

    def reset(self, seed=None):
        self.rng = np.random.default_rng(seed)
        self.i, self.q = 0, 0
        return self.state(0, 0)

    def step(self, a):
        bi, ai = self.actions[a]
        db, da = self.depths[bi], self.depths[ai]
        pb, pa = self.A * math.exp(-self.k * db) * self.dt, self.A * math.exp(-self.k * da) * self.dt
        buy = self.q < self.qmax and self.rng.random() < pb
        sell = self.q > -self.qmax and self.rng.random() < pa
        g = db * buy + da * sell
        self.q += int(buy) - int(sell)
        self.i += 1
        g -= self.phi * self.q**2 * self.dt
        done = self.i == self.n
        if done:
            g -= self.alpha * self.q**2
        return self.state(self.i, self.q), g, done


def q_learning_mm(env, episodes=4000, seed=0, power=0.6, eps=0.1):
    """Tabular Q-learning with a step size 1 / n(x, u)^power that decays with the visits of each pair (a constant
    step keeps chasing the fill noise)."""
    rng = np.random.default_rng(seed)
    nS = env.n_time * (2 * env.qmax + 1)
    Q, N = np.zeros((nS, len(env.actions))), np.zeros((nS, len(env.actions)))
    for ep in range(episodes):
        s, done = env.reset(seed * 1_000_003 + ep), False
        while not done:
            a = int(rng.integers(len(env.actions))) if rng.random() < eps else int(np.argmax(Q[s]))
            s2, g, done = env.step(a)
            target = g + (0.0 if done else Q[s2].max())
            N[s, a] += 1
            Q[s, a] += (target - Q[s, a]) / N[s, a] ** power
            s = s2
    return Q


def mm_policy(env, Q):
    """The greedy policy as a vectorised function of (t, q) arrays, in the form firm.invmm.simulate expects."""
    best = Q.argmax(1)

    def policy(t, q):
        i = np.minimum((np.asarray(t) / env.dt + 1e-9).astype(int), env.n - 1)
        s = np.minimum(env.n_time - 1, i * env.n_time // env.n) * (2 * env.qmax + 1) + (np.asarray(q) + env.qmax)
        a = best[np.clip(s, 0, len(best) - 1)]
        db = env.depths[np.array([env.actions[x][0] for x in np.atleast_1d(a)])]
        da = env.depths[np.array([env.actions[x][1] for x in np.atleast_1d(a)])]
        return db.reshape(np.shape(q)), da.reshape(np.shape(q))

    return policy


def mm_objective(res, phi, alpha):
    """Per-path value of the market maker's objective: P&L (inventory marked at the mid) minus the running and
    terminal inventory penalties."""
    return res["pnl"] - phi * res["q2_int"] - alpha * res["q_T"].astype(float) ** 2
