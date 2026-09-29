import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_dealterms as dt  # noqa: E402

P = dt.Programme(rebate=0.001, volume_share=0.10, symbols=10)


def test_daily_value():
    v = dt.daily_value(P, dt.Firm(0.05, 4, pad_loss=0.002, symbol_cost=1.0), 1000.0)
    assert v["padded_shares"] == 50.0 and v["rebate"] == pytest.approx(0.1) and v["padding"] == pytest.approx(0.1)
    assert v["quoting"] == 6.0 and v["net"] == pytest.approx(-6.0)
    w = dt.daily_value(P, dt.Firm(0.2, 20), 1000.0)
    assert w["net"] == pytest.approx(0.2) and w["padded_shares"] == 0.0


def test_breakeven_and_bargaining():
    a = dt.breakeven_share(P, lambda x: dt.Firm(x, 10, pad_loss=0.002, symbol_cost=0.0), 1000.0, 1e-4, 0.2)
    assert a == pytest.approx(0.05, abs=1e-6)                      # 0.1 x 0.001 = (0.1 - a) x 0.002
    assert dt.zopa(10.0, 2.0, 1.0, 1.0) == (3.0, 9.0)
    assert dt.nash_transfer(10.0, 2.0, 1.0, 1.0, beta=0.25) == pytest.approx(3.0 + 0.25 * 6.0)
    assert dt.venue_value(dt.Firm(0.05, 0), P, 1000.0, 0.5, 0.01) == pytest.approx(0.5)
