import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_deskplan as dp  # noqa: E402

ONE = dp.Plan((dp.Business("a", 10.0, 10.0),), ((1.0,),), 0.0, 0.0, 0.0, 11.0)


def test_p_meet_closed_form_and_simulation():
    assert math.isclose(dp.p_meet(ONE), 1 - dp._phi(0.1), rel_tol=1e-12)
    sim = dp.simulate(ONE, 20_000, np.random.default_rng(1))
    assert abs((sim["annual"] >= 11.0).mean() - dp.p_meet(ONE)) < 0.01
    assert (sim["max_drawdown"] >= 0).all()


def test_risk_multiple():
    lam = dp.risk_multiple(ONE, 0.75)
    z = dp._inv_phi(0.75)
    assert math.isclose(lam * (10 - z * 10), 11.0, rel_tol=1e-9)
    assert dp.risk_multiple(ONE, 0.9) == math.inf        # Sharpe 1 < z_0.9 = 1.28


def test_cascade_and_stats():
    p = dp.Plan((dp.Business("a", 10, 6), dp.Business("b", 5, 8)), ((1, 0.5), (0.5, 1)), 0, 0, 0, 15)
    s = dp.plan_stats(p)
    assert math.isclose(s["sigma"], math.sqrt(36 + 64 + 2 * 0.5 * 48))
    c = dp.cascade(p, 10.0)
    assert math.isclose(c["vol_budget"], 25.0 / dp._inv_phi(0.95))
    assert math.isclose(sum(c["stops"].values()), 10.0)
    rows = dp.plan_vs_actual(p, [1.0] * 12)
    assert rows[-1]["plan"] == 15 and rows[-1]["actual"] == 12
