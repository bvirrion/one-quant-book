import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_fundlaunch as fl  # noqa: E402


def test_fees_and_breakeven():
    t = fl.ff.FeeTerms(mgmt=0.02, perf=0.2)
    assert fl.annual_fees(100.0, 0.0, t) == pytest.approx(2.0)
    launch = fl.Launch(fixed_costs=1.0, variable_bp=0.0, mgmt=0.02, perf=0.0, revenue_share=0.5)
    assert fl.breakeven_aum(launch, 0.0) == pytest.approx(100.0)
    assert fl.years_for_t(2.0, 2.0) == 1.0 and fl.tstat(1.0, 4.0) == 2.0


def test_simulation_shapes_and_helpers():
    a, f = fl.simulate(fl.Launch(), seed=3, n_paths=100, months=24)
    assert a.shape == (100, 24) and np.isfinite(a).all()
    fm = fl.first_month(np.array([[1.0, 5.0, 12.0], [1.0, 2.0, 3.0]]), 10.0)
    assert list(fm) == [3, 0] and fl.prob_reach(np.array([[1.0, 12.0], [1.0, 2.0]]), 10.0, 2) == 0.5
    assert fl.seed_value(np.ones((1, 12)), 0.5, 0.0) == pytest.approx(12.0)
    assert fl.manager_value(np.zeros((1, 12)), np.ones((1, 12)), fl.Launch(fixed_costs=12.0), 0.0) == pytest.approx(0.0)
