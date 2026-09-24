"""Acceptance tests of the Book 2, Chapter 12 build (pass-through cash flows, prepayment, risk)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_prepay import (
    cash_flows,
    effective_risk,
    level_payment,
    price,
    psa_cpr,
    refi_cpr,
    roll_financing_rate,
    smm,
    wal,
)


def test_psa_ramp():
    assert math.isclose(psa_cpr(1), 0.002) and math.isclose(psa_cpr(2), 0.004)
    assert math.isclose(psa_cpr(30), 0.06) and math.isclose(psa_cpr(200), 0.06)
    assert math.isclose(psa_cpr(10, 2.0), 2 * psa_cpr(10))
    assert math.isclose(1 - (1 - smm(0.06)) ** 12, 0.06)


def test_no_prepayment_is_a_level_mortgage():
    flows = cash_flows(1e6, 0.06, 0.06, 360, 0, lambda a: 0.0)
    assert len(flows) == 360 and abs(flows[-1].balance) < 1e-6
    pay = level_payment(1e6, 0.005, 360)
    assert all(math.isclose(f.interest + f.scheduled, pay) for f in flows)


def test_principal_is_returned_and_price_is_par_at_the_coupon():
    for speed in (0.0, 1.0, 3.0):
        flows = cash_flows(1e6, 0.065, 0.06, 360, 0, lambda a, s=speed: psa_cpr(a, s))
        assert math.isclose(sum(f.scheduled + f.prepaid for f in flows), 1e6)
        assert math.isclose(price(flows, 0.06, 1e6), 100.0)
    fast = cash_flows(1e6, 0.065, 0.06, 360, 0, lambda a: psa_cpr(a, 3.0))
    slow = cash_flows(1e6, 0.065, 0.06, 360, 0, lambda a: psa_cpr(a, 0.5))
    assert wal(fast, 1e6) < wal(slow, 1e6)


def test_s_curve_and_negative_convexity():
    assert refi_cpr(-0.02) < refi_cpr(0.0) < refi_cpr(0.02) < 0.5
    def p(y):
        c = refi_cpr(0.065 - y - 0.005)
        return price(cash_flows(1e6, 0.065, 0.06, 360, 36, lambda a: c), y, 1e6)
    assert effective_risk(p, 0.06)["convexity"] < 0
    fixed = effective_risk(lambda y: price(cash_flows(1e6, 0.065, 0.06, 360, 36, lambda a: 0.1), y, 1e6), 0.06)
    assert fixed["convexity"] > 0


def test_roll():
    # no drop, no paydown: the roll finances at the coupon rate on par
    assert math.isclose(roll_financing_rate(100.0, 100.0, 0.06, 0.0), 0.06)
    assert roll_financing_rate(100.5, 100.25, 0.06, 0.01) < roll_financing_rate(100.5, 100.40, 0.06, 0.01)
