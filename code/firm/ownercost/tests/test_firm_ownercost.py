import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_ownercost as oc  # noqa: E402


def test_cost_and_split():
    o = oc.Owner("x", 1000.0, 1.0, 0.5, 0.5, 100.0)
    assert abs(oc.cost_bp(o) - 20.0) < 1e-12
    i, e = oc.split_bp(o)
    assert abs(i - 1e4 / 900) < 1e-9 and abs(e - 100.0) < 1e-9
    with pytest.raises(ValueError):
        oc.split_bp(oc.Owner("y", 1.0, 0.1, 0.0, 0.0))


def test_breakeven():
    a = oc.breakeven_assets(10, 0.4, 1.0, 20.0)
    assert abs(oc.internal_cost(10, 0.4, 1.0) - oc.external_cost(a, 20.0)) < 1e-9 and a == 2500.0
