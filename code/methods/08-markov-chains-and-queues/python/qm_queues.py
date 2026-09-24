"""Chapter 8 of Book 4: Markov chains and queues.

The bid-ask spread in ticks as a three-state chain; the M/M/1 queue and Little's law by simulation;
gambler's ruin by first-step analysis; the race between two best queues; and the probability that
an order at the back of an 800-lot queue fills before the other side's queue empties."""
from __future__ import annotations

import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/queues"))
from firm_queues import (
    bd_expected_exit_time,
    bd_hitting_probability,
    depletion_cdf,
    fill_time_cdf,
    generator,
    jump_chain,
    race,
    stationary,
)

LAM, NU, MU_MKT = 0.9, 1.0, 0.6         # per second: limit orders joining, orders leaving, market orders
LOT = 10                                 # lots per order
GRID = np.linspace(0.0, 1200.0, 2401)


def spread_chain() -> dict:
    """Spread of 1, 2 or 3 ticks: widening and narrowing rates per second."""
    rates = np.array([[0.0, 2.0, 0.0],
                      [5.0, 0.0, 1.0],
                      [0.5, 4.0, 0.0]])
    Q = generator(rates)
    pi = stationary(Q)
    return {"Q": Q, "pi": pi, "mean_ticks": float(pi @ np.array([1, 2, 3])), "jump": jump_chain(Q),
            "holding": 1 / -np.diag(Q)}


def mm1_simulation(rho: float, n: int = 200_000, seed: int = 1, mu: float = 1.0) -> dict:
    """M/M/1 with service rate mu: time-average number in system L, mean sojourn W, and lam W."""
    rng = np.random.default_rng(seed)
    lam = rho * mu
    arr = np.cumsum(rng.exponential(1 / lam, n))
    serv = rng.exponential(1 / mu, n)
    dep = np.empty(n)
    free = 0.0
    for i in range(n):
        start = max(arr[i], free)
        free = start + serv[i]
        dep[i] = free
    W = float(np.mean(dep - arr))
    ev_t = np.concatenate([arr, dep])
    ev_d = np.concatenate([np.ones(n), -np.ones(n)])
    order = np.argsort(ev_t, kind="stable")
    t, d = ev_t[order], ev_d[order]
    count = np.cumsum(d)
    L = float(np.sum(count[:-1] * np.diff(t)) / (t[-1] - t[0]))
    return {"L": L, "W": W, "lamW": lam * W, "L_theory": rho / (1 - rho), "W_theory": 1 / (mu - lam)}


def next_move_up(bid: int, ask: int) -> float:
    """P(the ask queue empties before the bid queue): the mid moves up first."""
    fa = depletion_cdf(LAM, NU, ask, GRID)
    fb = depletion_cdf(LAM, NU, bid, GRID)
    return race(fa, fb, GRID)


def fill_probability(ahead: int, ask: int) -> float:
    """P(an order with `ahead` orders in front of it at the best bid fills before the ask empties)."""
    return race(fill_time_cdf(ahead, NU, MU_MKT, GRID), depletion_cdf(LAM, NU, ask, GRID), GRID)


def simulate_fill(ahead: int, ask: int, n: int = 20_000, seed: int = 3) -> float:
    """Monte Carlo check of fill_probability: race the two chains event by event."""
    rng = np.random.default_rng(seed)
    wins = 0
    for _ in range(n):
        k, a, t_fill = ahead, ask, 0.0
        t_fill = rng.exponential(1 / NU, k).sum() + rng.exponential(1 / MU_MKT)
        t, q = 0.0, a
        while q > 0:
            t += rng.exponential(1 / (LAM + NU))
            if t >= t_fill:
                break
            q += 1 if rng.random() < LAM / (LAM + NU) else -1
        wins += q > 0 and t >= t_fill
    return wins / n


def problem() -> dict:
    p_fill = fill_probability(80, 20)
    e_fill = 80 / NU + 1 / MU_MKT
    t = GRID
    fa = depletion_cdf(LAM, NU, 20, t)
    med_ask = float(np.interp(0.5, fa, t))
    gr = bd_hitting_probability(LAM, NU, 40)
    return {
        "p_fill": p_fill, "p_fill_sim": simulate_fill(80, 20),
        "e_fill": e_fill, "p_fill_a40": fill_probability(80, 40), "p_fill_a80": fill_probability(80, 80),
        "p_fill_k20": fill_probability(20, 20), "p_up_80_20": next_move_up(80, 20), "p_up_20_20": next_move_up(20, 20),
        "median_ask_depletion": med_ask, "p_ask_by_60": float(np.interp(60.0, t, fa)),
        "p_ask_ever": float(fa[-1]), "p_reach40_from20": float(gr[20]),
        "exit_time_20": float(bd_expected_exit_time(LAM, NU, 40)[20]),
        "mean_depletion_20": 20 / (NU - LAM),
    }
