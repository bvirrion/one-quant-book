import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_crbook import CRBConfig, central, desk_by_desk, hedge_cost, pooled, simulate_desks  # noqa: E402

CFG = CRBConfig(names=10, days=30)


def test_offsetting_desks_cost_nothing_pooled():
    sim = simulate_desks(CRBConfig(names=10, days=30, desks=2))
    sim["flows"][1] = -sim["flows"][0]
    assert np.allclose(pooled(sim, CFG), 0.0) and (desk_by_desk(sim, CFG) > 0).all()


def test_full_rate_is_pooled_and_carries_nothing():
    sim = simulate_desks(CFG)
    c = central(sim, CFG, 1.0, False)
    assert np.allclose(c["stock_cost"], pooled(sim, CFG)) and np.allclose(c["pnl"], 0.0)


def test_futures_remove_market_risk():
    cfg = CRBConfig(names=10, days=30, factor_vol=(0.01, 0.0, 0.0), idio_vol=0.0)
    sim = simulate_desks(cfg)
    assert np.allclose(central(sim, cfg, 0.2, True)["pnl"], 0.0, atol=1e-6)
    assert central(sim, cfg, 0.2, False)["pnl"].std() > 0


def test_cost_by_hand():
    sim = simulate_desks(CFG)
    q = np.zeros(10)
    q[3] = 1e6
    s, v = sim["sigma"][3], sim["adv"][3]
    assert math.isclose(hedge_cost(q, sim, CFG), 1e6 * (3e-4 + 0.7 * s * math.sqrt(1e6 / v)))
