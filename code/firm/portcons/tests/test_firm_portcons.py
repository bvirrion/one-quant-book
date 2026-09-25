import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_portcons import Problem, ir_ex_ante, trade_list


def _setup(n=40, seed=0):
    rng = np.random.default_rng(seed)
    X = np.column_stack([np.ones(n), rng.standard_normal(n)])
    F = np.diag([4e-4, 1e-4])
    spec = rng.uniform(1e-4, 4e-4, n)
    alpha = 1e-3 * rng.standard_normal(n)
    return alpha, X, F, spec


def test_unconstrained_matches_closed_form_and_neutrality():
    alpha, X, F, spec = _setup()
    p = Problem(alpha, X, F, spec, gamma=5.0)
    r = p.solve()
    assert np.allclose(r["w"], np.linalg.solve(5.0 * p.Sigma, alpha), atol=1e-7)
    p2 = Problem(alpha, X, F, spec, gamma=5.0)
    p2.equality(np.ones(40), 0.0, "dollar")
    p2.neutral_factors([1], ["style"])
    r2 = p2.solve()
    assert abs(r2["w"].sum()) < 1e-9 and abs(X[:, 1] @ r2["w"]) < 1e-9
    # KKT: alpha = gamma Sigma w + sum lambda_k a_k, with lambda the shadow prices
    lam = np.linalg.lstsq(np.column_stack([np.ones(40), X[:, 1]]), alpha - 5.0 * p2.Sigma @ r2["w"], rcond=None)[0]
    assert np.allclose(np.abs(lam), np.abs([r2["duals"]["dollar"], r2["duals"]["style"]]), atol=1e-8)


def test_bounds_gross_turnover_and_shadow_prices():
    alpha, X, F, spec = _setup(seed=1)
    base = Problem(alpha, X, F, spec, gamma=2.0)
    base.equality(np.ones(40), 0.0, "dollar")
    free = base.solve()
    p = Problem(alpha, X, F, spec, gamma=2.0)
    p.equality(np.ones(40), 0.0, "dollar")
    p.bounds(-0.05, 0.05, "name limit")
    p.gross(1.0, "gross")
    r = p.solve()
    assert np.abs(r["w"]).max() <= 0.05 + 1e-7 and r["gross"] <= 1.0 + 1e-7
    assert r["duals"]["gross"] > 0 and r["binding"]["gross"] == 1 and r["objective"] < free["objective"]
    eps = 1e-3                                                             # the shadow price is the marginal value
    p3 = Problem(alpha, X, F, spec, gamma=2.0)
    p3.equality(np.ones(40), 0.0, "dollar")
    p3.bounds(-0.05, 0.05, "name limit")
    p3.gross(1.0 + eps, "gross")
    assert abs((p3.solve()["objective"] - r["objective"]) / eps - r["duals"]["gross"]) < 0.02 * r["duals"]["gross"]
    t = Problem(alpha, X, F, spec, gamma=2.0, w0=r["w"])
    t.equality(np.ones(40), 0.0, "dollar")
    t.turnover(0.1, "turnover")
    rt = t.solve()
    assert rt["turnover"] <= 0.1 + 1e-7 and rt["binding"]["turnover"] == 1
    k = Problem(alpha, X, F, spec, gamma=2.0, w0=r["w"])
    k.equality(np.ones(40), 0.0, "dollar")
    k.turnover_penalty(1.0)
    assert np.allclose(k.solve()["w"], r["w"], atol=1e-6)                 # a large cost: no trade


def test_liquidity_ir_and_trades():
    alpha, X, F, spec = _setup(seed=2)
    p = Problem(alpha, X, F, spec, gamma=2.0)
    adv = np.full(40, 1e6)
    adv[0] = 1e4
    p.liquidity(adv, 0.1, 1e7, "liquidity")
    r = p.solve()
    assert abs(r["w"][0]) <= 1e-4 + 1e-9
    assert abs(ir_ex_ante(alpha, p.Sigma, r["w"]) - r["ir"]) < 1e-12
    tl = trade_list([0.01, -0.02, 0.0], [0.0, 0.0, 0.0], 1e6, [50.0, 20.0, 10.0], ["a", "b", "c"])
    assert tl == [("b", -1000), ("a", 200)]


def test_kkt_pull_and_ir_decomposition_add_up():
    alpha, X, F, spec = _setup(seed=3)
    p = Problem(alpha, X, F, spec, gamma=3.0, w0=np.zeros(40))
    p.equality(np.ones(40), 0.0, "dollar")
    p.neutral_factors([1], ["style"])
    p.bounds(-0.02, 0.02, "name limit")
    p.gross(0.6, "gross")
    p.turnover_penalty(1e-4)
    r = p.solve()
    G = sum(r["pull"].values())
    assert np.allclose(alpha - 3.0 * p.Sigma @ r["w"], G, atol=1e-8)
    d = p.ir_decomposition(r)
    assert abs(d["ir_eff"] ** 2 - 9.0 * r["w"] @ p.Sigma @ r["w"]) < 1e-8 * d["ir_free"] ** 2
    assert abs(sum(d["delta"].values()) - (d["ir_free"] ** 2 - d["ir_eff"] ** 2)) < 1e-10
    assert set(d["delta"]) == {"dollar", "style", "name limit", "gross", "turnover penalty"}
