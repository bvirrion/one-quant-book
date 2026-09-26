"""firm.execcontrol -- execution as a control problem (build of One Quant Book 10, chapter 15).

Discrete time, n steps of length tau; holdings x_k still to sell; a sale u_k at step k pays the temporary impact eta u_k
/ tau per share; the price drifts at alpha_k per unit time (a signal, alpha_{k+1} = phi alpha_k + noise) and diffuses
with volatility sigma. All schedules plug into firm.acexec's Scheduler interface where they are static.

API (stable):
    lqr_signal(n, tau, eta, sigma, lam, phi, terminal=1e6)   feedback gains K_k: u_k = K_k[0] x_k + K_k[1] alpha_k,
                                         from the Riccati recursion of the linear-quadratic problem min E sum
                                         (eta u^2 / tau + lam sigma^2 tau x^2 - tau alpha x), with x_n forced to zero
    simulate(policy, X, n, tau, eta, sigma, alpha0, phi, s_alpha, seed, paths)   costs per share against the arrival
                                         price of a policy u_k = policy(k, x, alpha, dp) over simulated paths
    OWScheduler(X, rho, T)               Obizhaeva-Wang: blocks of X / (rho T + 2) at both ends, a constant rate between
    aim(k0, a, sigma, T, n)              an adaptive policy: the Almgren-Chriss trajectory from the current holdings
                                         with urgency k0 exp(a dP / (sigma sqrt T)): a seller speeds up in the money
    liquidity_dp(X, n, tau, eta, sigma, lam, stay, grid)   stochastic liquidity: two regimes (normal, dry)
                                         with temporary impact eta[0], eta[1] and staying probabilities stay[0],
                                         stay[1] (multiples of 0.1), solved by Book 4's firm.dpsolve on (holdings,
                                         regime); returns the policy
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

for _c in ("acexec", "dpsolve"):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / _c))
from firm_acexec import Scheduler  # noqa: E402
from firm_dpsolve import backward_induction  # noqa: E402


def lqr_signal(n: int, tau: float, eta: float, sigma: float, lam: float, phi: float,
               terminal: float = 1e6):
    q = np.array([[lam * sigma**2 * tau, -tau / 2], [-tau / 2, 0.0]])
    r = eta / tau
    a = np.array([[1.0, 0.0], [0.0, phi]])
    b = np.array([[-1.0], [0.0]])
    p = np.array([[terminal, 0.0], [0.0, 0.0]])
    gains = []
    for _ in range(n):
        k = np.linalg.solve(r + b.T @ p @ b, b.T @ p @ a)          # u = -k z
        p = q + a.T @ p @ a - a.T @ p @ b @ k
        gains.append(-k.ravel())
    return gains[::-1]


def simulate(policy, x_total: float, n: int, tau: float, eta: float, sigma: float, phi: float, s_alpha: float,
             seed: int = 1, paths: int = 2000) -> np.ndarray:
    rng = np.random.default_rng(seed)
    innov = s_alpha * math.sqrt(max(1 - phi**2, 0.0))
    costs = np.empty(paths)
    for j in range(paths):
        x, alpha, dp, cash = x_total, s_alpha * rng.standard_normal(), 0.0, 0.0
        for k in range(n):
            u = x if k == n - 1 else float(np.clip(policy(k, x, alpha, dp), -x_total, x))
            cash += u * (dp - eta * u / tau)                         # sale price relative to arrival
            x -= u
            dp += alpha * tau + sigma * math.sqrt(tau) * rng.standard_normal()
            alpha = phi * alpha + innov * rng.standard_normal()
        costs[j] = -cash / x_total
    return costs


class OWScheduler(Scheduler):
    def __init__(self, x_total: float, rho: float, horizon: float):
        self.x, self.rho, self.h = x_total, rho, horizon
        self.block = x_total / (rho * horizon + 2)

    def targets(self, times):
        t = np.asarray(times, float)
        left = self.x - self.block - self.rho * self.block * np.clip(t, 0, self.h)
        return np.where(t <= 0, self.x, np.where(t >= self.h, 0.0, left))


def aim(k0: float, a: float, sigma: float, horizon: float, n: int):
    """A policy u(k, x, alpha, dp): the Almgren-Chriss trajectory from the current holdings
    over the time left, with urgency k0 exp(a dp / (sigma sqrt(horizon)))."""
    tau = horizon / n

    def policy(k, x, alpha, dp):
        left = horizon - k * tau
        kk = k0 * math.exp(a * dp / (sigma * math.sqrt(horizon)))
        if kk * left < 1e-9:
            return x * tau / left
        if kk * left > 30:                           # the ratio of sinh without overflow
            return x * (1 - math.exp(-kk * tau))
        return x - x * math.sinh(kk * (left - tau)) / math.sinh(kk * left)
    return policy


def liquidity_dp(x_total: float, n: int, tau: float, eta, sigma: float, lam: float, stay, grid: int = 101,
                 terminal: float = 1e6) -> dict:
    xs = np.linspace(0.0, x_total, grid)
    off = 2 * x_total + 1.0
    states = np.concatenate([xs, xs + off])
    controls = np.linspace(0.0, x_total, grid)
    nodes = 10
    same = [int(round(10 * s)) for s in stay]

    def split(s):
        reg = (s >= off).astype(int)
        return s - reg * off, reg

    def reward(t, s, u):
        x, reg = split(s)
        u = np.minimum(u, x)
        e = np.where(reg == 0, eta[0], eta[1])
        return -(e * u**2 / tau + lam * sigma**2 * tau * (x - u) ** 2)

    def transition(t, s, u):
        x, reg = split(s)
        x1 = x - np.minimum(u, x)
        out = np.empty(s.shape + (nodes,))
        for j in range(nodes):
            stay_now = np.where(reg == 0, j < same[0], j < same[1])
            reg1 = np.where(stay_now, reg, 1 - reg)
            out[..., j] = x1 + reg1 * off
        return out, np.full(nodes, 1.0 / nodes)

    def final(s):
        x, _ = split(s)
        return -terminal * x**2
    res = backward_induction(states, controls, n, reward, transition, final)
    return {"grid": xs, "policy_normal": res["policy"][:, :grid], "policy_dry": res["policy"][:, grid:],
            "value": res["values"]}
