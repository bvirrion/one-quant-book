"""Acceptance tests of the Chapter 26 build."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_gex import (
    YEAR_MINUTES,
    Holding,
    dealer_book_from_open_interest,
    delta,
    gamma,
    gamma_shares_per_pct,
    hedge_trade,
)


def test_gamma_is_the_derivative_of_delta_and_the_same_for_calls_and_puts():
    s, k, t, v, h = 100.0, 101.0, 5 / 252, 0.2, 1e-4
    num = (delta(s + h, k, t, v, "C") - delta(s - h, k, t, v, "C")) / (2 * h)
    assert gamma(s, k, t, v) == pytest.approx(num, rel=1e-6)
    nump = (delta(s + h, k, t, v, "P") - delta(s - h, k, t, v, "P")) / (2 * h)
    assert nump == pytest.approx(num, rel=1e-6)


def test_at_the_money_gamma_grows_like_one_over_root_time():
    g_month = gamma(100.0, 100.0, 21 / 252, 0.16)
    g_hour = gamma(100.0, 100.0, 60 / YEAR_MINUTES, 0.16)
    assert g_hour / g_month == pytest.approx(math.sqrt(21 * 390 / 60), rel=0.01)


def test_hedging_direction():
    long_gamma = [Holding(100.0, "C", 1 / 252, 0.16, +1000)]
    short_gamma = [Holding(100.0, "C", 1 / 252, 0.16, -1000)]
    assert hedge_trade(long_gamma, 100.0, 101.0) < 0 < hedge_trade(short_gamma, 100.0, 101.0)
    approx = gamma_shares_per_pct(long_gamma, 100.0)
    exact = -hedge_trade(long_gamma, 100.0, 100.1) * 10
    assert approx == pytest.approx(exact, rel=0.02) and approx > 0


def test_expired_options_have_delta_one_or_zero():
    assert delta(101.0, 100.0, 0.0, 0.2, "C") == 1.0 and delta(99.0, 100.0, 0.0, 0.2, "C") == 0.0
    assert delta(99.0, 100.0, 0.0, 0.2, "P") == -1.0 and gamma(100.0, 100.0, 0.0, 0.2) == 0.0


def test_the_sign_assumption_decides_everything():
    oi = [(95.0, "P", 5000), (100.0, "C", 3000), (105.0, "C", 4000)]
    a = gamma_shares_per_pct(dealer_book_from_open_interest(oi, 2 / 252, 0.2, {"C": +1, "P": -1}), 100.0)
    b = gamma_shares_per_pct(dealer_book_from_open_interest(oi, 2 / 252, 0.2, {"C": -1, "P": -1}), 100.0)
    assert a > 0 > b
