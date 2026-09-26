import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_etfmm as fe  # noqa: E402


def test_fair_values_by_hand():
    assert math.isclose(fe.closed_fair(100.0, 1.0, 0.015, -0.005), 100.0 * 1.015 * 0.995)
    G = np.array([0.0, 0.01, 0.02])
    assert math.isclose(fe.pricing_basket([100.0, 50.0], [0, 1], [1.0, 2.0], G, 2),
                        0.5 * (100.0 * 1.02 + 50.0 * (1 + 2.0 * 0.01)))


def test_creation_decision():
    # 50,000 shares at 100: a 1,250 fee is 0.25 bp; 2 bp of basket cost
    act, edge = fe.creation_decision(100.05, 100.0, 50000, 1250.0, 2.0)
    assert act == "create" and math.isclose(edge, 2500.0 - 1250.0 - 1000.0, abs_tol=1e-6)
    assert fe.creation_decision(99.95, 100.0, 50000, 1250.0, 2.0)[0] == "redeem"
    assert fe.creation_decision(100.01, 100.0, 50000, 1250.0, 2.0) == ("none", 0.0)


def test_market_paths():
    mk = fe.Market(seed=1, days=20, freeze=(10, 13))
    t = 5000
    assert np.all(mk.t_last[t] <= t) and math.isclose(mk.nav[t], float(np.mean(mk.last[t])))
    assert np.all(mk.last[t] == mk.last[mk.t_last[t], np.arange(mk.n)])
    err_nav = np.abs(mk.nav - mk.true)[mk.stress].mean()
    err_b = np.abs(mk.basket - mk.true)[mk.stress].mean()
    assert err_b < 0.2 * err_nav
    assert mk.age[mk.stress].mean() > 3 * mk.age[~mk.stress].mean()


def test_market_maker():
    mk = fe.Market(seed=2, days=20, freeze=(10, 13))
    f = np.isin(np.arange(mk.days), range(*mk.freeze))
    res = {}
    for est in ("nav", "basket"):
        for hedge in ("none", "future"):
            r = fe.run_mm(mk, est, hedge, "redeem")
            assert math.isclose(sum(r[k].sum() for k in ("spread", "arb", "hedge", "flatten", "inventory")),
                                r["total"].sum(), rel_tol=1e-9, abs_tol=1e-3)
            res[est, hedge] = r
    assert res["basket", "future"]["total"][f].sum() > res["nav", "future"]["total"][f].sum()
    held = {h: fe.run_mm(mk, "basket", h, "hold") for h in ("none", "future")}
    assert held["future"]["inventory"][~f].std() < 0.6 * held["none"]["inventory"][~f].std()
