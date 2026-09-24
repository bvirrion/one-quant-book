"""Acceptance tests of the Book 2, Chapter 3 build (fixed-coupon bonds)."""
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_bond import Bond, add_months, bootstrap_par, par_yield, thirty_360, zero_price

D = dt.date


def test_cfr_example_a_on_a_coupon_date():
    b = Bond(8.75, D(2020, 5, 15))
    s = D(1990, 5, 15)
    assert b.accrued(s) == 0.0
    assert round(b.clean_price(0.0884, s, treasury=True), 6) == 99.057893
    assert round(b.clean_price(0.0884, s), 6) == 99.057893          # conventions agree on coupon dates


def test_cfr_example_d_between_coupons():
    b = Bond(9.50, D(1995, 11, 15))
    s = D(1985, 11, 29)
    assert round(b.accrued(s), 6) == 0.367403
    assert round(b.clean_price(0.0954, s, treasury=True), 6) == 99.730918
    assert b.clean_price(0.0954, s) != pytest.approx(99.730918, abs=1e-6)   # street differs off-coupon


def test_month_end_schedule():
    b = Bond(4.0, D(2028, 8, 31))
    prev, nxt = b.coupon_dates(D(2028, 3, 10))
    assert prev == D(2028, 2, 29) and nxt[0] == D(2028, 8, 31)
    assert add_months(D(2027, 2, 28), 6, eom=True) == D(2027, 8, 31)


def test_price_yield_round_trip_and_par():
    b = Bond(4.25, D(2036, 8, 15))
    s = D(2026, 9, 25)
    for y in (0.02, 0.0425, 0.07):
        assert b.yield_from_clean(b.clean_price(y, s), s) == pytest.approx(y, abs=1e-12)
    on_coupon = D(2026, 8, 15)
    assert b.clean_price(0.0425, on_coupon) == pytest.approx(100.0, abs=1e-10)


def test_dv01_and_convexity_match_bumps():
    b = Bond(4.25, D(2036, 8, 15))
    s, y, h = D(2026, 9, 25), 0.042, 1e-4
    r = b.risk(y, s)
    up, dn = b.dirty_price(y + h, s), b.dirty_price(y - h, s)
    assert r["dv01"] == pytest.approx((dn - up) / 2, rel=1e-6)
    assert r["convexity"] == pytest.approx((up + dn - 2 * r["dirty"]) / (h * h) / r["dirty"], rel=1e-4)
    assert r["macaulay"] < 10.0 and r["modified"] < r["macaulay"]


def test_zero_coupon_duration_is_its_maturity():
    b = Bond(0.0, D(2036, 8, 15))
    r = b.risk(0.04, D(2026, 8, 15))
    assert r["macaulay"] == pytest.approx(10.0)
    assert r["dirty"] == pytest.approx(zero_price(0.04, 10.0))


def test_thirty_360():
    assert thirty_360(D(2026, 1, 31), D(2026, 7, 31)) == 0.5
    assert thirty_360(D(2026, 2, 28), D(2026, 8, 31)) == pytest.approx(183 / 360)


def test_bootstrap_reprices_par():
    pars = [0.040, 0.041, 0.042, 0.043]
    dfs = bootstrap_par(pars)
    for k in range(1, 5):
        assert par_yield(dfs[:k]) == pytest.approx(pars[k - 1])
