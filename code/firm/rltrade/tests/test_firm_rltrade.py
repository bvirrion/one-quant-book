import itertools
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_rltrade import ACEnv, MMEnv, _mask, ac_objective, dqn_schedule, grid_optimum, train_dqn  # noqa: E402


def test_rewards_sum_to_the_objective():
    env = ACEnv()
    plan = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
    env.reset(0)
    total, xs = 0.0, [1.0]
    for u in plan:
        _, g, _ = env.step(u)
        total += g
        xs.append(env.left / env.lots)
    assert abs(-total - ac_objective(np.array(xs), env, env.eta)) < 1e-12


def test_masking():
    m = _mask([3, 5], [False, True], 21)
    assert m[0].nonzero().flatten().tolist() == [0, 1, 2, 3] and m[1].nonzero().flatten().tolist() == [5]
    env = ACEnv()
    env.reset(0)
    for _ in range(9):
        env.step(0)
    env.step(0)
    assert env.left == 0


def test_grid_optimum_beats_enumeration():
    env = ACEnv(n=4, lots=4)
    best = ac_objective(grid_optimum(env), env, env.eta)
    for plan in itertools.product(range(5), repeat=3):
        if sum(plan) <= 4:
            left = 4 - np.cumsum(plan)
            xs = np.r_[1.0, left / 4, 0.0]
            assert ac_objective(xs, env, env.eta) >= best - 1e-12


def test_dqn_deterministic_and_beats_twap():
    env = ACEnv()
    n1, l1 = train_dqn(env, 300, seed=1)
    n2, l2 = train_dqn(ACEnv(), 300, seed=1)
    assert l1 == l2
    h = dqn_schedule(env, n1)
    assert ac_objective(h, env, env.eta) < ac_objective(np.linspace(1, 0, 11), env, env.eta)


def test_domain_randomisation_draws_eta_in_range():
    env = ACEnv(eta_range=(0.0005, 0.002))
    etas = [env.reset(s) is not None and env.eta_ep for s in range(200)]
    assert 0.0005 <= min(etas) and max(etas) <= 0.002 and np.std(np.log(etas)) > 0.3


def test_mm_fill_rates():
    """Away from the inventory bounds, |dq| is 1 when exactly one side fills: probability 2 p (1 - p)."""
    env = MMEnv(qmax=1000)
    a = env.actions.index((2, 2))
    moves, steps = 0, 0
    for ep in range(200):
        env.reset(ep)
        done = False
        while not done:
            q0 = env.q
            _, _, done = env.step(a)
            moves += abs(env.q - q0)
            steps += 1
    p = env.A * np.exp(-env.k * env.depths[2]) * env.dt
    assert abs(moves / steps - 2 * p * (1 - p)) < 0.01
