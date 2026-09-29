import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_bonuspool as bp  # noqa: E402


def test_pools_and_rules():
    assert bp.pool_from_profit(100, 60, 10, 0.2) == 6.0 and bp.pool_from_profit(50, 60, 0, 0.2) == 0.0
    assert list(bp.formulaic([10, -5], 0.15)) == [1.5, 0.0]
    assert np.allclose(bp.risk_adjusted([10, 3], [20, 40], 0.15, 0.2), [1.4, 0.0])
    d = bp.discretionary([[10.0, 0.0], [10.0, 0.0]], 6.0, 10.0, 5.0, 5.0)
    assert math.isclose(d.sum(), 6.0) and d[0] > d[1]


def test_shrinkage_weight():
    s = bp.shrunk_skill([[20.0]], 10.0, 0.0, 10.0)
    assert math.isclose(s[0], 10.0)
    s4 = bp.shrunk_skill([[20.0]] * 4, 10.0, 0.0, 10.0)
    assert math.isclose(s4[0], 20.0 * 100 / (100 + 25))


def test_deferral_balance():
    p = bp.DeferralPlan(0.6, 4)
    assert np.allclose(bp.schedule(10.0, p), [6.0, 1.0, 1.0, 1.0, 1.0])
    assert math.isclose(bp.unvested([10.0] * 6, p, 5), 10.0 * 0.4 * (1 + 0.75 + 0.5 + 0.25))
    assert math.isclose(bp.malus([10.0], p, 0, 0.5), 2.0)


def test_luck_formulas():
    assert math.isclose(bp.luck_share_linear(0.4, 1.0), 1 / 1.16)
    t = bp.years_for_correlation(0.4, 1.0, 0.8)
    assert math.isclose(0.16 / (0.16 + 1 / t), 0.64)
