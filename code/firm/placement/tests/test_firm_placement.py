import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "agentmkt"))
from firm_placement import (  # noqa: E402
    BookModel,
    Cross,
    Post,
    SliceExecutor,
    cross_cost,
    imbalance_threshold,
    q_policy,
    qlearn,
    simulate,
    solve,
)

M = BookModel(lam=1.0, theta=0.05, mu=0.6, fresh=(0.3, 0.3, 0.2, 0.1, 0.1), depth2=3.0)


def test_cross_cost_walks_the_book():
    assert cross_cost(2, 5, 3.0) == 1.0 and cross_cost(4, 2, 3.0) == 0.5 * 2 + 1.5 * 2
    assert cross_cost(8, 2, 3.0) == 0.5 * 2 + 1.5 * 3 + 2.5 * 3


def test_dp_value_matches_its_own_simulation_and_beats_static_rules():
    plan = solve(M, 3, 20.0, dt=0.2, n_max=15, a_max=15)
    k = len(plan.cross) - 1

    def dp(r, n, a, kk):
        return np.array([plan.cross[kk][ri, ni, max(ai, 1)] for ri, ni, ai in zip(r, n, a, strict=True)])
    mc = simulate(M, dp, 3, 20.0, paths=20_000, seed=3, n_cap=15, a_cap=15)
    assert abs(mc.mean() - plan.fresh_value[k][3]) < 0.05
    wait = simulate(M, lambda r, n, a, kk: np.zeros(len(r), bool), 3, 20.0, paths=20_000, seed=3, n_cap=15, a_cap=15)
    now = simulate(M, lambda r, n, a, kk: np.ones(len(r), bool), 3, 20.0, paths=20_000, seed=3, n_cap=15, a_cap=15)
    assert mc.mean() <= min(wait.mean(), now.mean()) + 0.02
    # a thin ask and a long bid: cross; a thick ask and a short bid: wait
    assert plan.cross[k][1, 15, 1] and not plan.cross[k][1, 0, 15]
    c = plan.cross[k][1]
    assert (c[1:] >= c[:-1]).all() and (c[:, 2:] <= c[:, 1:-1]).all()    # more ahead, thinner ask: cross
    wide = solve(BookModel(0.8, 0.05, 1.2, tuple([1 / 15] * 15), 3.0), 1, 20.0, dt=0.1, n_max=15, a_max=15)
    cut, agree = imbalance_threshold(wide, 1)
    assert 0 < cut < 1 and agree > 0.9 and imbalance_threshold(plan, 1)[0] == 1.0


def test_qlearning_approaches_the_dp():
    plan = solve(M, 2, 10.0, dt=0.2, n_max=15, a_max=15)
    q = qlearn(M, 2, 10.0, episodes=60_000, batch=2_000, seed=2, n_cap=15, a_cap=15)
    cost = simulate(M, q_policy(q), 2, 10.0, paths=20_000, seed=5, n_cap=15, a_cap=15).mean()
    assert cost < plan.fresh_value[-1][2] + 0.25


def test_executor_completes_slices():
    from firm_agentmkt import T0, PopulationConfig, session
    from firm_exchsim import SEC
    cfg = PopulationConfig(lo_rate=2.0, near=0.5, cancel=0.02, depth=10, noise=0.6, mo_lots=2.0)
    for pol in (Cross(), Post(0, True)):
        ex = SliceExecutor([(T0 + 60 * SEC, "B", 800, 30.0), (T0 + 120 * SEC, "S", 800, 30.0)], pol)
        res, _ = session(cfg, 200.0, 4, agents=[ex])
        f = res.agents["placer"].fills
        buys = sum(x[5] for x in f if x[3] > 0)
        sells = sum(x[5] for x in f if x[3] < 0)
        assert buys >= 800 and sells >= 800 and len(ex.log) == 2
