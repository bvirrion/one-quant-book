import pathlib
import sys
from dataclasses import replace

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_buildbuy as bb  # noqa: E402


def test_costs_and_npc():
    b = bb.Build(wage=1.0, kappa=0.0, dev_engineers=2, dev_years=1, maint_engineers=1, infra=0.5)
    assert bb.build_costs(b, 3) == [2.0, 1.5, 1.5]
    y = bb.Buy(licence=1.0, escalator=0.1, integration_fee=0.5, integration_engineers=1, support_engineers=0, wage=1.0,
               kappa=0.0)
    assert bb.buy_costs(y, 2) == pytest.approx([2.5, 1.1])
    assert bb.npc([1.1], 0.1) == pytest.approx(1.0)


def test_breakevens():
    b, y = bb.Build(), bb.Buy()
    w = bb.breakeven_wage(b, y, 7, 0.08)
    assert bb.npc(bb.build_costs(replace(b, wage=w), 7), 0.08) == pytest.approx(
        bb.npc(bb.buy_costs(replace(y, wage=w), 7), 0.08))
    assert bb.breakeven_horizon(b, y, 0.08) is not None


def test_switch_option_is_non_negative_and_grows_with_risk():
    y = bb.Buy()
    v1 = bb.switch_value(y, 6, 0.08, 1.3, 0.2, 1.0)[2]
    v2 = bb.switch_value(y, 6, 0.08, 1.3, 0.5, 1.0)[2]
    assert 0 <= v1 < v2
    rows = bb.tornado(lambda p: p["a"] * 2 + p["b"], {"a": 1.0, "b": 1.0})
    assert rows[0][0] == "a" and rows[0][1:] == pytest.approx((1.6 + 1.0, 2.4 + 1.0))
