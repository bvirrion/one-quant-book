"""firm.queues -- Markov chains and queues sized for order books (One Quant Book 4, chapter 8).

A best-price queue, counted in orders, is modelled as a birth-death chain: limit orders join at
rate `birth`, market orders and cancellations remove orders at rate `death`. The functions give
the stationary law of a chain, first-step hitting probabilities and expected times, the law of the
time to empty a queue (by uniformisation of the generator), and races between queues.

API (stable):
    generator(q_rates)                         -> generator matrix from an off-diagonal rate matrix
    stationary(Q)                              -> stationary distribution of a finite chain
    jump_chain(Q)                              -> transition matrix of the embedded jump chain
    bd_hitting_probability(birth, death, n)    -> P(reach n before 0) from each state 0..n
    bd_expected_exit_time(birth, death, n)     -> E[time to reach 0 or n] from each state
    depletion_cdf(birth, death, start, t, n_max) -> P(queue empty by time t), t a grid
    race(cdf_a, cdf_b, t)                      -> P(A happens before B) for independent times
    fill_time_cdf(k, nu, mu, t)                -> P(k orders ahead removed, then a market order, by t)
    thomas(a, b, c, d)                         -> tridiagonal solve
"""
from __future__ import annotations

import math

import numpy as np


def generator(rates: np.ndarray) -> np.ndarray:
    """Q with the given off-diagonal rates and rows summing to zero."""
    q = np.array(rates, dtype=float)
    np.fill_diagonal(q, 0.0)
    np.fill_diagonal(q, -q.sum(axis=1))
    return q


def stationary(Q: np.ndarray) -> np.ndarray:
    """Solve pi Q = 0, sum(pi) = 1 (irreducible finite chain)."""
    n = Q.shape[0]
    a = np.vstack([Q.T, np.ones(n)])
    b = np.concatenate([np.zeros(n), [1.0]])
    return np.linalg.lstsq(a, b, rcond=None)[0]


def jump_chain(Q: np.ndarray) -> np.ndarray:
    """P[i, j] = q_ij / q_i for j != i: where the chain goes when it leaves i."""
    rates = -np.diag(Q)
    P = Q / rates[:, None]
    np.fill_diagonal(P, 0.0)
    return P


def thomas(a: np.ndarray, b: np.ndarray, c: np.ndarray, d: np.ndarray) -> np.ndarray:
    """Solve a tridiagonal system: a sub-diagonal (a[0] unused), b diagonal, c super-diagonal
    (c[-1] unused), right-hand side d."""
    n = b.size
    cp, dp = np.empty(n), np.empty(n)
    cp[0], dp[0] = c[0] / b[0], d[0] / b[0]
    for i in range(1, n):
        m = b[i] - a[i] * cp[i - 1]
        cp[i] = c[i] / m if i < n - 1 else 0.0
        dp[i] = (d[i] - a[i] * dp[i - 1]) / m
    x = np.empty(n)
    x[-1] = dp[-1]
    for i in range(n - 2, -1, -1):
        x[i] = dp[i] - cp[i] * x[i + 1]
    return x


def _interior(birth, death, n):
    i = np.arange(1, n)
    lam = np.broadcast_to(np.asarray(birth(i) if callable(birth) else birth, float), i.shape)
    mu = np.broadcast_to(np.asarray(death(i) if callable(death) else death, float), i.shape)
    return lam, mu


def bd_hitting_probability(birth, death, n: int) -> np.ndarray:
    """h_i = P(reach n before 0 | start at i) by first-step analysis:
    (lam_i + mu_i) h_i = lam_i h_{i+1} + mu_i h_{i-1}, h_0 = 0, h_n = 1."""
    lam, mu = _interior(birth, death, n)
    a, b, c = -mu, lam + mu, -lam
    d = np.zeros(n - 1)
    d[-1] = lam[-1]                       # h_n = 1 moved to the right-hand side
    return np.concatenate([[0.0], thomas(a, b, c, d), [1.0]])


def bd_expected_exit_time(birth, death, n: int) -> np.ndarray:
    """m_i = E[time to hit 0 or n | start at i]: (lam_i + mu_i) m_i - lam_i m_{i+1} - mu_i m_{i-1} = 1."""
    lam, mu = _interior(birth, death, n)
    m = thomas(-mu, lam + mu, -lam, np.ones(n - 1))
    return np.concatenate([[0.0], m, [0.0]])


def _uniformised(absorbed: np.ndarray, rate: float, t: np.ndarray) -> np.ndarray:
    """sum_k Poisson(k; rate t) absorbed[k] for each t: the uniformisation series."""
    ks = np.arange(absorbed.size)
    lg = np.array([math.lgamma(x + 1) for x in ks])
    out = np.empty(t.size)
    for j, tj in enumerate(t):
        if tj == 0:
            out[j] = absorbed[0]
        else:
            out[j] = float(np.sum(np.exp(-rate * tj + ks * math.log(rate * tj) - lg) * absorbed))
    return out


def depletion_cdf(birth: float, death: float, start: int, t: np.ndarray, n_max: int = 400) -> np.ndarray:
    """P(T_0 <= t) for a birth-death queue with constant rates, absorbing at 0 and reflecting at
    n_max, by uniformisation: with L = birth + death and P = I + Q / L the jump matrix of the
    uniformised chain, P(absorbed by t) = sum_k Poisson(k; L t) P(absorbed after k jumps)."""
    L = birth + death
    t = np.asarray(t, float)
    p = np.zeros(n_max + 1)
    p[start] = 1.0
    k_max = int(L * t.max() + 12 * math.sqrt(L * t.max() + 1) + 20)
    absorbed = np.empty(k_max + 1)
    for k in range(k_max + 1):
        absorbed[k] = p[0]
        new = np.empty_like(p)
        new[0] = p[0] + death / L * p[1]
        new[1:-1] = death / L * p[2:] + birth / L * np.concatenate([[0.0], p[1:-2]])
        new[-1] = birth / L * (p[-2] + p[-1])
        p = new
    return _uniformised(absorbed, L, t)


def race(cdf_a: np.ndarray, cdf_b: np.ndarray, t: np.ndarray) -> float:
    """P(T_a < T_b) = int (1 - F_b) dF_a, for independent times, on the grid t (trapezoid)."""
    dfa = np.diff(cdf_a)
    surv_b = 1 - 0.5 * (cdf_b[1:] + cdf_b[:-1])
    return float(np.sum(dfa * surv_b))


def fill_time_cdf(k: int, nu: float, mu: float, t: np.ndarray) -> np.ndarray:
    """P(fill by t) for an order with k orders ahead: k removals at rate nu (market orders plus
    cancellations ahead), then a market order at rate mu: the absorption time of the pure-death
    chain k ahead -> ... -> 0 ahead -> filled, by uniformisation."""
    t = np.asarray(t, float)
    L = max(nu, mu)
    k_max = int(L * t.max() + 12 * math.sqrt(L * t.max() + 1) + 20)
    p = np.zeros(k + 2)                   # index j = j orders removed; index k + 1 = filled
    p[0] = 1.0
    rate = np.full(k + 2, nu)
    rate[k] = mu                          # the last step: a market order hits our order
    rate[k + 1] = 0.0
    absorbed = np.empty(k_max + 1)
    for j in range(k_max + 1):
        absorbed[j] = p[-1]
        move = p * rate / L
        p = p - move
        p[1:] += move[:-1]
    return _uniformised(absorbed, L, t)
