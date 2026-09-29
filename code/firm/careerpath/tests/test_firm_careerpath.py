"""Acceptance tests for firm.careerpath."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_careerpath as fc  # noqa: E402

JOB = fc.Job(base=100.0, award=120.0, deferral=0.5, vest_years=3, pay_month=2)


def test_forfeiture_by_month():
    assert fc.unvested(JOB) == pytest.approx(0.5 * 120 * 2)
    jan, mar = fc.forfeited(JOB, 1), fc.forfeited(JOB, 3)
    assert jan["unpaid"] == 120 and mar["unpaid"] == 0 and jan["accrued"] == 0 and mar["accrued"] == 20
    assert fc.forfeited(JOB, 2)["total"] > mar["total"]      # the day before payment is the worst month to leave


def test_move_and_raise():
    c = fc.move_cost(JOB, 3, 3, 0, 6, paid_noncompete=False, q=1.0, s=1.0)
    assert c["out_months"] == 9 and c["lost_award"] == 90 and c["lost_base"] == 50 and c["buyout"] == 120
    assert c["net"] == pytest.approx(140 + 90 + 50 - 120)
    assert fc.breakeven_raise(JOB, 3, 2, notice_m=3) == pytest.approx(fc.move_cost(JOB, 3, 3)["net"] / 440)


def test_chain():
    ch = fc.Chain(("a", "b"), ((0.0, 1.0), (0.0, 1.0)), (1.0, 2.0))
    s = fc.simulate(ch, "a", 3, 5, np.random.default_rng(0))
    assert (s[:, 0] == 0).all() and (s[:, 1:] == 1).all()
    assert fc.pay_paths(ch, s)[0].tolist() == [1.0, 2.0, 2.0]
    with pytest.raises(ValueError):
        fc.simulate(fc.Chain(("a",), ((0.5,),), (1.0,)), "a", 1, 1, np.random.default_rng(0))


def test_spinouts():
    class E:
        def __init__(self, r):
            self.relation = r

    class G:
        edges = [E("spun out of"), E("founders traded on the floor of")]

    assert len(fc.spinouts(G())) == 1
