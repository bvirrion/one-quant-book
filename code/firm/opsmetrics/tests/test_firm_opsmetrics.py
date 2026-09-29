import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_opsmetrics as om  # noqa: E402


def test_queue_matches_erlang_c():
    for lam, mu, c in ((7.5, 2.0, 5), (15.0, 1.5, 12), (3.0, 1.0, 4)):
        assert abs(om.p_wait(lam, mu, c) - om.erlang_c(lam, mu, c)) < 1e-8
    with pytest.raises(ValueError):
        om.mmc_stationary(10.0, 1.0, 10)


def test_late_and_staffing():
    assert abs(om.p_late(1.0, 1.0, 60, 2.0) - math.exp(-2.0)) < 1e-9
    assert om.p_late(15, 1.5, 12, 4.0) < om.p_late(15, 1.5, 11, 4.0) < om.p_late(15, 1.5, 11, 2.5)
    c = om.staff_for(15, 1.5, 2.5, 0.95)
    assert c == 12 and 1 - om.p_late(15, 1.5, c, 2.5) >= 0.95 > 1 - om.p_late(15, 1.5, c - 1, 2.5)
    with pytest.raises(ValueError):
        om.staff_for(15, 1.5, 1.0, 0.95)
    a = om.ageing(15, 1.5, 12, [0, 1, 2])
    assert abs(sum(a) - 1) < 1e-12 and all(x >= 0 for x in a)


def test_collateral_and_kri():
    csa = om.Csa(10.0, 0.5)
    assert abs(om.call(25.3, 14.6, csa) - 0.7) < 1e-9 and om.call(24.4, 14.6, csa) == 0.0
    assert om.call(5.0, 3.0, csa) == -3.0 and om.disputed(25.3, 24.4, 0.02) and not om.disputed(25.3, 25.2, 0.02)
    assert om.fail_cost(10, 5e6, 1.0, 2, 1500) == 25000.0
    assert [om.kri(v, 10, 25) for v in (5, 14, 30)] == ["green", "amber", "red"]
    assert [om.kri(v, 95, 90) for v in (97, 93, 85)] == ["green", "amber", "red"]
