import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from clearing_demo import Trade, Waterfall, initial_margin, net_obligations, netting_efficiency, random_trades


def test_everything_nets_to_zero_across_members():
    sh, cash = net_obligations(random_trades(500, 6, 1))
    assert sum(cash.values()) == pytest.approx(0.0, abs=1e-6)
    for sym in ("S0", "S1", "S2", "S3", "S4"):
        assert sum(m.get(sym, 0) for m in sh.values()) == 0


def test_round_trip_nets_out():
    t = [Trade("A", "B", "X", 100, 10.0), Trade("B", "A", "X", 100, 10.0)]
    assert netting_efficiency(t) == pytest.approx(1.0)


def test_efficiency_grows_with_activity():
    assert netting_efficiency(random_trades(5000, 8, 3)) > netting_efficiency(random_trades(20, 8, 3))


def test_margin_scales_with_sqrt_days():
    assert initial_margin(100, 0.05, 2) / initial_margin(100, 0.05, 1) == pytest.approx(2**0.5)


def test_waterfall_order_and_conservation():
    w = Waterfall(120, 30, 20, 400, 400)
    a = w.allocate(180)
    assert list(a.values()) == [120, 30, 20, 10, 0, 0]
    assert sum(w.allocate(2000).values()) == 2000 and w.allocate(2000)["uncovered"] == 1030
