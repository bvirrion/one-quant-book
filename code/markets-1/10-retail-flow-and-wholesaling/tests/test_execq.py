import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from execq import EXCHANGE, RETAIL, max_payment, simulate, stats


def test_identity_holds_trade_by_trade():
    s, p, m = simulate(RETAIL, 50_000, 1)
    st = stats(s, p, m[60.0])
    assert st["effective"] == pytest.approx(st["realised"] + st["impact"])


def test_effective_spread_reflects_price_improvement():
    s, p, m = simulate(RETAIL, 50_000, 2)
    assert stats(s, p, m[1.0])["effective"] == pytest.approx(0.80)
    s, p, m = simulate(EXCHANGE, 50_000, 2)
    assert stats(s, p, m[1.0])["effective"] == pytest.approx(1.00)


def test_long_horizon_impact_is_informed_share_times_move():
    s, p, m = simulate(EXCHANGE, 400_000, 3)
    assert stats(s, p, m[300.0])["impact"] == pytest.approx(0.35 * 3.0, rel=0.05)


def test_retail_flow_is_worth_paying_for_and_exchange_flow_is_not():
    assert max_payment(1.0, RETAIL, 0.10) == pytest.approx(0.55)
    assert max_payment(1.0, EXCHANGE, 0.10) < 0
