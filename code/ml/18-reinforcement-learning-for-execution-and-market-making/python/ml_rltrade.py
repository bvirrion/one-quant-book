"""Reinforcement learning for execution and market making (One Quant Book 12, chapter 18).

Execution: an Almgren-Chriss liquidation (10 steps, 20 lots, eta 0.001, sigma 0.02, lambda 10; objective in basis
points) learned by a deep Q-network, with the shaped reward and with the zero-mean P&L noise left in, and with domain
randomisation of the impact (eta drawn log-uniformly over a factor of three either way) and an observation of the impact
seen in the agent's own fills; every schedule is scored exactly against the Almgren-Chriss optimum of three worlds.
Market making: the Cartea-Jaimungal model learned by tabular Q-learning, scored with firm.invmm's simulator on common
random numbers against the exact optimum, the Avellaneda-Stoikov approximation and a constant symmetric quote."""
from __future__ import annotations

import functools
import os
import pathlib
import sys

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402

_FIRM = pathlib.Path(__file__).resolve().parents[3] / "firm"
for _c in ("rltrade", "acexec", "invmm"):
    sys.path.insert(0, str(_FIRM / _c))
from firm_acexec import discrete  # noqa: E402
from firm_invmm import CJSolution, as_policy, cj_policy, simulate, symmetric  # noqa: E402
from firm_rltrade import (  # noqa: E402
    ACEnv,
    MMEnv,
    ac_objective,
    dqn_schedule,
    grid_optimum,
    mm_objective,
    mm_policy,
    q_learning_mm,
    train_dqn,
)

ENV = ACEnv()
ETA = ENV.eta
WORLDS = {"model": ETA, "impact x3": 3 * ETA, "impact /3": ETA / 3}


def bp(x):
    return 1e4 * x


def optimum(eta):
    return discrete(ENV.X, ENV.T, ENV.n, eta, ENV.sigma, ENV.lam)


@functools.lru_cache(maxsize=1)
def agents():
    """name -> function(eta) -> holdings. Closed forms, TWAP and three deep Q-networks."""
    net, _ = train_dqn(ACEnv(), 1500, seed=0)
    env_dr = ACEnv(eta_range=(ETA / 3, 3 * ETA))
    net_dr, _ = train_dqn(env_dr, 3000, seed=0)
    env_noise = ACEnv(noise=True)
    net_noise, _ = train_dqn(env_noise, 1500, seed=0)
    return {"Almgren-Chriss (model)": lambda eta: optimum(ETA),
            "TWAP": lambda eta: np.linspace(ENV.X, 0.0, ENV.n + 1),
            "DQN": lambda eta: dqn_schedule(ACEnv(), net, eta),
            "DQN, noisy reward": lambda eta: dqn_schedule(env_noise, net_noise, eta),
            "DQN, randomised": lambda eta: dqn_schedule(env_dr, net_dr, eta)}


@functools.lru_cache(maxsize=1)
def execution():
    """Objective of each world's optimum and each agent's gap to it (basis points)."""
    out = {}
    for w, eta in WORLDS.items():
        opt = bp(ac_objective(optimum(eta), ENV, eta))
        out[w] = {"optimum": opt} | {k: bp(ac_objective(f(eta), ENV, eta)) - opt for k, f in agents().items()}
    out["grid"] = bp(ac_objective(grid_optimum(ENV), ENV, ETA)) - out["model"]["optimum"]
    return out


def benchmark_twap():
    return bp(ac_objective(np.linspace(1.0, 0.0, ENV.n + 1), ENV, ETA))


# ---------------------------------------------------------------------------------------------------- market making
MM = MMEnv()


@functools.lru_cache(maxsize=1)
def market_making(paths=5000, seed=7):
    """Mean objective (P&L minus inventory penalties), its standard error, P&L standard deviation, mean absolute
    closing inventory and number of fills per path, on common random numbers."""
    sol = CJSolution(MM.A, MM.k, MM.phi, MM.alpha, MM.qmax, MM.T, n=200)
    pols = {"Cartea-Jaimungal optimum": cj_policy(sol),
            "Avellaneda-Stoikov, gamma 0.1": as_policy(0.1, MM.sigma, MM.k, MM.T), "constant 1/k": symmetric(1 / MM.k)}
    for n in (2000, 8000):
        pols[f"Q-learning, {n} episodes"] = mm_policy(MM, q_learning_mm(MM, n, seed=0))
    out = {}
    for k, p in pols.items():
        r = simulate(p, MM.T, MM.dt, MM.sigma, MM.A, MM.k, paths, seed=seed, qmax=MM.qmax)
        o = mm_objective(r, MM.phi, MM.alpha)
        out[k] = {"objective": float(o.mean()), "se": float(o.std() / np.sqrt(paths)), "pnl sd": float(r["pnl"].std()),
                  "abs q_T": float(np.abs(r["q_T"]).mean()), "fills": float(r["fills"].mean())}
    out["cj depths at t=0"] = sol.depths(0.0, np.array([-5, 0, 5]))
    return out


@functools.lru_cache(maxsize=1)
def linear_policy_search():
    """Exercise 7: depths c + d q on the bid and c - d q on the ask (a long market maker bids wider and offers
    tighter), (c, d) chosen on a grid by the mean objective on 2,000 paths (seed 11), then scored on the chapter's
    5,000 common paths (seed 7)."""
    def pol(c, d):
        def f(t, q):
            q = np.asarray(q, float)
            return np.maximum(c + d * q, 0.0), np.maximum(c - d * q, 0.0)
        return f

    grid = [(round(c, 2), round(d, 3)) for c in np.arange(0.55, 0.81, 0.05) for d in (0.0, 0.01, 0.02, 0.03, 0.04)]
    score = {}
    for c, d in grid:
        r = simulate(pol(c, d), MM.T, MM.dt, MM.sigma, MM.A, MM.k, 2000, seed=11, qmax=MM.qmax)
        score[(c, d)] = float(mm_objective(r, MM.phi, MM.alpha).mean())
    best = max(score, key=score.get)
    r = simulate(pol(*best), MM.T, MM.dt, MM.sigma, MM.A, MM.k, 5000, seed=7, qmax=MM.qmax)
    return best, float(mm_objective(r, MM.phi, MM.alpha).mean())
