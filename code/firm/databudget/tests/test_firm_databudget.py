import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_databudget as db  # noqa: E402


def test_costs_and_budget():
    p = db.Product("x", "c", per_user=2.0, per_device=1.0, flat=5.0, enterprise=10.0)
    assert db.annual_cost(p, db.Usage(3, 2)) == 13.0 and db.annual_cost(p, db.Usage(3, 2), True) == 15.0
    q = db.Product("y", "c", per_user=1.0)
    assert db.budget([p, q], {"x": db.Usage(3, 2), "y": db.Usage(4, 0)}) == {"c": 17.0}
    with pytest.raises(ValueError):
        db.annual_cost(q, db.Usage(1, 0), True)
    assert db.enterprise_breakeven(db.Product("z", "c", per_user=3.0, enterprise=10.0)) == 4


def test_audit_exposure():
    a = db.audit_exposure(120.0, 0.5, 1.0, 0.0)
    assert a["principal"] == pytest.approx(120.0) and a["interest"] == pytest.approx(0.0)
    b = db.audit_exposure(120.0, 0.5, 1.0, 0.01)
    assert b["interest"] > 0 and b["total"] == pytest.approx(sum(10 * 1.01 ** k for k in range(12)))


def test_alt_breakeven_wraps_vendoreval():
    assert db.alt_breakeven(0.02, 100.0, 0.0, 1e9, 1) == pytest.approx(2.0)
